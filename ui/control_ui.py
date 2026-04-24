# sample UI module, need to add all of the display modes and many more events
# The functions in this module are samples, merely meant to understand the flow between modules
import logging
import os
import json
import time


class ControlUI:
    """Framework for the UI class that will drive the UI and publish events to the driver based on button presses"""
    def __init__(self, event_bus, config):
        self.bus = event_bus
        self.config = config # For DEV MODE and Pathing
        self.logger = logging.getLogger("ui")

        #Brightness states
        settings = self._load_ui_settings()
        self.simulate_brightness = settings.get("brightness", 100)
        self.on_pi = self.is_raspberry_pi()
        self.backlight_path = self._detect_backlight_path()

        # Sleep states
        self.sleep_enabled = settings.get("sleep_enabled", False)
        self.sleep_time = settings.get("sleep_time", 30)  # default 30 seconds for testing
        self.sleep_mode = False
        self.last_activity = time.time()

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

    def _load_ui_settings(self):
        path = self.config.ui_settings
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                default_settings = {"brightness": 30, "sleep_enabled": False, "sleep_time": 3600}
                with open(path, "w") as f:
                    json.dump(default_settings, f, indent=2)
                return default_settings
        return {}

    def _save_ui_settings(self, settings):
        path = self.config.ui_settings
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(settings, f, indent=2)

    def is_raspberry_pi(self):
        try:
            with open("/proc/cpuinfo", "r") as f:
                return "Raspberry Pi" in f.read()
        except FileNotFoundError:
            return False

    def preview_brightness(self, value):
        if self.on_pi:
            self._simulate_brightness(value)
        else:
            self._simulate_brightness(value)

    def set_brightness(self, value):
        if self.on_pi:
            self._simulate_brightness(value)
        else:
            self._simulate_brightness(value)

    def _write_brightness(self, percent):
        try:
            if not self.backlight_path or not os.path.exists(self.backlight_path):
                print("Brightness error: No backlight device found")
                return

            max_path = os.path.join(self.backlight_path, "max_brightness")
            val_path = os.path.join(self.backlight_path, "brightness")

            with open(max_path, "r") as f:
                max_val = int(f.read().strip())

            new_val = int(max_val * (percent / 100))

            with open(val_path, "w") as f:
                f.write(str(new_val))

        except Exception as e:
            print("Brightness error:", e)

    def _detect_backlight_path(self):
        base = "/sys/class/backlight"
        if not os.path.exists(base):
            return None

        entries = os.listdir(base)
        if not entries:
            return None

        # Pick the first entry (most Pi images only have one)
        return os.path.join(base, entries[0])

    def _simulate_brightness(self, value):
        self.simulate_brightness = value
        print(f"[SIMULATION] Brightness set to {value}%")

        # Save to settings file
        settings = self._load_ui_settings()
        settings["brightness"] = value
        self._save_ui_settings(settings)


    def get_dimming_alpha(self):
        if self.sleep_mode:
            return 255  # full black for sleep

        # Prevent the screen from going completely black
        MIN_BRIGHTNESS = 10  # 0–100 scale

        # Clamp brightness so it never goes below the minimum
        effective_brightness = max(self.simulate_brightness, MIN_BRIGHTNESS)

        # Convert brightness → alpha
        return int((100 - effective_brightness) * 2.55)

    def set_sleep_enabled(self, enabled):
        self.sleep_enabled = enabled
        settings = self._load_ui_settings()
        settings["sleep_enabled"] = enabled
        self._save_ui_settings(settings)

    def set_sleep_time(self, time_seconds):
        self.sleep_time = time_seconds
        settings = self._load_ui_settings()
        settings["sleep_time"] = time_seconds
        self._save_ui_settings(settings)

    def update_activity(self):
        self.last_activity = time.time()
        self.sleep_mode = False

    def check_sleep(self):
        if self.sleep_enabled and not self.sleep_mode:
            if time.time() - self.last_activity > self.sleep_time:
                self.sleep_mode = True
 
