import logging
import uuid
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from json import load

from click import password_option

from polling_agent import (
    PollingAgent, 
    Node, 
    PersistentConnection, 
    LinuxMetricsProvider, 
    WindowsMetricsProvider
)
from event_bus import EventBus

# Set a standard logging format to be used by all modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)

# Control module linking application service
class Driver:
    """The driver owns the polling agent, and routes touchscreen control events to polling agent functions"""
    def __init__(self, event_bus: EventBus, config):
        self.config = config #FOR DEV MODE
        self.polling_agent = None
        self.metrics_queue = None
        self.control_executor = None
        self.running = False
        self.event_bus = event_bus

    def start(self):
        """Function to start the monitoring system"""
        logging.info("[Driver] Starting system...")

        # Create polling queue
        self.metrics_queue = Queue()

        # Create high level executor for background functions
        self.control_executor = ThreadPoolExecutor(max_workers=4)

        # Initialize polling agent
        self.polling_agent = PollingAgent(self.metrics_queue)

        # Driver listens for UI control events
        self.event_bus.subscribe(
            # If event bus has event of this type
            "UPDATE_POLLING_RATE",
            # update_polling_rate requires a handler function because its payload has multiple components that must be parsed
            self.update_polling_rate
        )

        self.event_bus.subscribe(
            "REMOVE_NODE",
            # remove_node needs a handler function as well because its payload must be parsed as well
            self._handle_remove_node
        )

        self.event_bus.subscribe(
            "STOP_SYSTEM",
            self.stop_system
        )

        self.event_bus.subscribe(
            "PAIRING_NODE_READY",
            self.add_node
        )

        self.event_bus.subscribe(
            "PAUSE_POLLING",
             self._on_pause_polling
        )

        self.event_bus.subscribe(
            "UPDATE_DEVICE_NAME",
            self.update_device_name
        )

        # Load targets and launch polling
        nodes = load_targets(self.config)
        self.polling_agent.launch_nodes(nodes)

        self.running = True

        # Start background services
        self.control_executor.submit(self._dispatch_metrics)

        logging.info("[Driver] System running.")

    def update_polling_rate(self, payload):
        """Function to update the polling rate of a particular node"""
        host = payload["host"]
        new_rate = payload["poll_rate"]
        with open(self.config.decrypted_list, "r") as f:
            data = load(f)

        for item in data.values():
            if item.get("name") == host:
                item["polling_frequency"] = new_rate

        with open(self.config.decrypted_list, "w") as f:
            import json
            json.dump(data, f, indent=4)

        self.reload_config()

        # Acknowledge polling rate update
        self.event_bus.publish("ACK_UPDATE_POLLING_RATE", {
            "host": host,
            "poll_rate": new_rate
        })

    def _handle_remove_node(self, payload):
        """Handler function that formats data for remove_node"""
        self.remove_node(payload["node"])

    def remove_node(self, node_name: str):
        """System-level node removal"""

        success = False
        logging.info("[Driver] Removing node: %s", node_name)

        # Stop the running worker
        if self.polling_agent:
            self.polling_agent.remove_node(node_name)

        # Open the device list
        try:
            with open(self.config.decrypted_list, "r") as f:
                data = load(f)

            removed_key = None

            # Get the key of the node to remove
            for key, item in data.items():
                if item.get("name") == node_name:
                    removed_key = key
                    break

            if removed_key:
                del data[removed_key]

                with open(self.config.decrypted_list, "w") as f:
                    import json
                    json.dump(data, f, indent=4)

                logging.info(
                    "[Driver] Node '%s' removed from configuration",
                    node_name
                )
                success = True
            else:
                logging.warning(
                    "[Driver] Node '%s' not found in configuration",
                    node_name
                )
                success = False

        except Exception as e:
            logging.error(
                "[Driver] Failed removing node from JSON: %s",
                e
            )
            success = False

        # ACK Remove Node
        self.event_bus.publish("ACK_REMOVE_NODE", {
            "node": node_name,
            "success": success
        })

        # ACK Pause Node

        # reconcile system
        self.reload_config()

    def stop_system(self, payload=None):
        """Function to safely shutdown the driver"""
        logging.info("[Driver] Shutting down...")

        self.running = False

        # Stop polling nodes first
        if self.polling_agent:
            self.polling_agent.shutdown()

        # Stop event bus second
        if self.event_bus:
            self.event_bus.stop()

        # Stop control threads last
        if self.control_executor:
            self.control_executor.shutdown(wait=True, cancel_futures=True)

        logging.info("[Driver] Shutdown complete.")

    def add_node(self, node_config: dict):
        """Add a node dynamically by updating device_list.json"""
        node_name = node_config.get("name")

        logging.info(
            "[Driver] Adding node: %s",
            node_name
        )

        with open(self.config.decrypted_list, "r") as f:
            data = load(f)

        # Prevent duplicates by name
        for item in data.values():
            if item.get("name") == node_name:
                logging.warning(
                    "Node '%s' already exists — skipping",
                    node_name
                )
                self.event_bus.publish("ACK_ADD_NODE", {
                    "name": node_name,
                    "success": False,
                    "reason": "duplicate",
                })
                return

        # Create a new uuid string for the node
        new_id = str(uuid.uuid4())

        # Create new entry for the new id
        data[new_id] = node_config

        with open(self.config.decrypted_list, "w") as f:
            import json
            json.dump(data, f, indent=4)

        logging.info(
            "[Driver] Node '%s' added — triggering reload",
            node_name
        )

        # optional immediate reconcile
        self.reload_config()
        self.event_bus.publish("SYNC_VAULT", {})
        self.event_bus.publish("ACK_ADD_NODE", {
            "name": node_name,
            "success": True,
        })

    # This function allows the UI to subscribe to metric events
    def _dispatch_metrics(self):
        """Background function to push metrics to the event bus"""
        while self.running:
            try:
                metric_event = self.metrics_queue.get(timeout=1)
            except Exception:
                continue

            if not self.running:
                break

            self.event_bus.publish("METRIC_EVENT", metric_event)

    def reload_config(self):
        """Helper function that reloads configuration and reconciles nodes"""
        logging.info("[Driver] Reloading configuration")

        nodes = load_targets(self.config)
        self.polling_agent.reconcile(nodes)

        # Publish device list to UI
        with open (self.config.decrypted_list, "r") as f:
            device_list = load(f)
        self.event_bus.publish("DEVICE_LIST_UPDATED", device_list)

    def _on_pause_polling(self, payload):
        device = payload["device"]
        paused = payload["paused"]

        # Persist pause state so it survives config reloads and restarts.
        try:
            with open(self.config.decrypted_list, "r") as f:
                data = load(f)

            updated = False
            for item in data.values():
                if item.get("name") == device:
                    item["polling_paused"] = bool(paused)
                    updated = True
                    break

            if updated:
                with open(self.config.decrypted_list, "w") as f:
                    import json
                    json.dump(data, f, indent=4)
            else:
                logging.warning(f"Pause request for unknown device in config: {device}")
        except Exception as e:
            logging.error(f"Failed to persist pause state for {device}: {e}")

        # Update internal node state
        node_entry = self.polling_agent.workers.get(device)
        if node_entry:
            node, future = node_entry
            node.polling_paused = paused
            logging.info(f"Polling for {device} paused = {paused}")
        else:
            logging.warning(f"Pause request for unknown device: {device}")

        # Send ACK back to UI
        self.event_bus.publish("ACK_POLLING_PAUSED", {
            "device": device,
            "paused": paused
        })

    def update_device_name(self, payload):
        old_name = payload["old_name"]
        new_name = payload["new_name"]
        with open(self.config.decrypted_list, "r") as f:
            data = load(f)

        updated = False
        for item in data.values():
            if item.get("name") == old_name:
                item["name"] = new_name
                updated = True

        if updated:
            with open(self.config.decrypted_list, "w") as f:
                import json
                json.dump(data, f, indent=4)

            self.reload_config()

            self.event_bus.publish("ACK_UPDATE_DEVICE_NAME", {
                "old_name": old_name,
                "new_name": new_name
            })



# Load and initialize targets from device_list.json
def load_targets(config) -> list:
    """Function to load and initialize targets from device_list.json"""
    nodes = []

    
    try:
        with open(config.decrypted_list, "r") as file:
            data = load(file)
    except FileNotFoundError:
        logging.warning("[Driver] device_list.json not found (First Boot). Starting with 0 nodes.")
        return [] # Return an empty list so the Driver doesn't crash!
    

    items = data.values()

    for item in items:
        host = item.get("hostname")
        user = item.get("user")
        name = item.get("name")
        os_type = (item.get("operating_system") or "").lower()
        poll_freq = int(item.get("polling_frequency", 5))
        polling_paused = bool(item.get("polling_paused", False))
        password = item.get("Pword")  # Add this line

        conn = PersistentConnection(
            host=host, 
            user=user,
            key_path=config.ssh_key_ram, # Feeds private key
            password=password # Feeds password (if applicable)
        )
        
        if(os_type == "linux"):
            provider = LinuxMetricsProvider(conn)
        elif(os_type == "windows"):
            provider = WindowsMetricsProvider(conn)
        else:
            # Gracefully handle error if OS is unsupported
            logging.warning(
                "Skipping node '%s' — unsupported OS '%s'",
                name,
                os_type,
            )
            continue

        nodes.append(Node(
            name=name,
            provider=provider,
            interval=poll_freq,
            polling_paused=polling_paused,
        ))
    # Returns list of node objects
    return nodes