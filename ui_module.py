# sample UI module, need to add all of the display modes and many more events
# The functions in this module are samples, merely meant to understand the flow between modules
import logging

class UI:
    """Framework for the UI class that will drive the UI and publish events to the driver based on button presses"""
    def __init__(self, event_bus):
        self.bus = event_bus
        self.logger = logging.getLogger("ui")

    # Currently this command is executed in main, but later, it will be executed by run_ui function in this class
    def change_polling_rate(self, host, new_rate):
        """Function to change the polling rate of a host"""
        self.logger.info(
                "Request polling change for %s → %s sec",
                host,
                new_rate
            )
        # Publishes a control event that the driver is subscribed to
        # driver sees event type, routes the request to a function, passes the data as arguments
        self.bus.publish(
            "UPDATE_POLLING_RATE",
            {
                "host": host,
                "poll_rate": new_rate
            }
        )
    
    def add_node(self):
        """Function to add a new target node to be polled, no input for now, just hard coded"""
        self.bus.publish(
            "ADD_NODE",
            {
                "name": "nas",
                "hostname": "192.168.1.20",
                "user": "alec",
                "operating_system": "linux",
                "polling_frequency": 10
            }
        )

    def remove_node(self):
        self.bus.publish(
            "REMOVE_NODE",
            {
                "node": "nas"
            }
        )

    def stop_system(self):
        """UI Function to remove node, will be linked with a button, for now, just hardcoded"""
        self.bus.publish(
            "STOP_SYSTEM",
            None
        )