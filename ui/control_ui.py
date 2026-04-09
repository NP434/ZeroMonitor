# sample UI module, need to add all of the display modes and many more events
# The functions in this module are samples, merely meant to understand the flow between modules
import logging
import os


class ControlUI:
    """Framework for the UI class that will drive the UI and publish events to the driver based on button presses"""
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config # For DEV MODE and Pathing
        self.logger = logging.getLogger("ui")

        #Brightness states
        self.simulate_brightness = 50
        self.on_pi = self.is_raspberry_pi()
        self.backlight_path = "/sys/class/backlight/rpi_backlight"

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
    
    def add_node(self,node_config:dict):
        """Function to add a new target node to be polled, no input for now, just hard coded"""
        self.bus.publish(
            "UI_ADD_NODE", node_config
        )

    def remove_node(self, device_name):
        """UI Function to remove node, will be linked with a button, for now, just hardcoded"""
        self.bus.publish(
            "REMOVE_NODE",
            {
                "node": device_name
            }
        )

    def stop_system(self):
        """UI Function to shutdown system"""
        self.bus.publish(
            "STOP_SYSTEM",
            None
        )

    def pause_polling(self, device_name, paused):
        self.bus.publish("PAUSE_POLLING", {
            "device": device_name,
            "paused": paused
        })

    def change_device_name(self, old_name, new_name):
        self.bus.publish("UPDATE_DEVICE_NAME", {
            "old_name": old_name,
            "new_name": new_name
        })

    def is_raspberry_pi(self):
        try:
            with open("/proc/cpuinfo", "r") as f:
                return "Raspberry Pi" in f.read()
        except FileNotFoundError:
            return False

    def preview_brightness(self, value):
        if self.on_pi:
            self._write_brightness(value)
        else:
            self._simulate_brightness(value)

    def set_brightness(self, value):
        if self.on_pi:
            self._write_brightness(value)
        else:
            self._simulate_brightness(value)

    def _write_brightness(self, percent):
        try:
            max_path = os.path.join(self.backlight_path, "max_brightness")
            val_path = os.path.join(self.backlight_path, "brightness")

            with open(max_path, "r") as f:
                max_val = int(f.read().strip())

            new_val = int(max_val * (percent / 100))

            with open(val_path, "w") as f:
                f.write(str(new_val))

        except Exception as e:
            print("Brightness error:", e)

    def _simulate_brightness(self, value):
        self.simulated_brightness = value
        print(f"[SIMULATION] Brightness set to {value}%")