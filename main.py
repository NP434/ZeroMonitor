# Entry point for the program
import time
import argparse
import os
import logging

# --- LOGGING SET UP (MUST BE FIRST) ---
# Create the hidden logs folder if it doesn't exist
# Updoot Test #4
os.makedirs("logs", exist_ok=True)

# Configure the global logging rules
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/system.log"), 
        logging.StreamHandler() # Keeps printing to the terminal
    ]
)
logging.info("=" * 60)


from event_bus import EventBus
from driver import Driver
from security_manager import SecurityManager
from network_manager import NetworkManager
from update_manager import UpdateManager
from datainterpreter import DataInterpreter
from ui.display_ui import DisplayUI
from ui.control_ui import ControlUI
from Pairing.pairing_control import ControlPairing
from paths import Config

# Creates dev_mode tag
parser = argparse.ArgumentParser(description="Zero Monitor System")
parser.add_argument("--dev", action="store_true", help="Run in local Dev Mode")
args = parser.parse_args()

# Initialize the paths based on the tag
config = Config(dev_mode=args.dev)

# Create and start a single event bus that is shared between all modules
bus = EventBus()
bus.start()

# etc....
# EVERY CLASS must update __init__ for config
# self.config = config # Store the master paths

# Create and start an instance of driver, passing it the shared event bus
driver = Driver(bus, config=config)
driver.start()

# Instantiate DataInterpreter to process metrics from the polling agent
data_interpreter = DataInterpreter(bus, config=config, json_filepath=config.cache_file)

# Create the UI backend control interface (publishing control events)
ui_control = ControlUI(bus, config=config)
pair_control = ControlPairing(bus, config=config)
security = SecurityManager(event_bus=bus, config=config)
network = NetworkManager(bus=bus, config=config)
updater = UpdateManager(event_bus=bus, config=config)

# Create the Pygame UI (subscribes to backend events and renders screens)
ui_display = DisplayUI(config=config, bus=bus, ui_control=ui_control)
ui_display.run()

# Example commands from the UI, this will be handled by UI_Controller in the future
ui_control.change_polling_rate("pihole", 30)
ui_control.add_node()
time.sleep(20)
ui_control.remove_node()

# Keep alive loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    driver.stop_system()
