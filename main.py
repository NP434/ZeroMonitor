# Entry point for the program
import time
from event_bus import EventBus
from driver import Driver
from ui.display_ui import DisplayUI
from ui.control_ui import ControlUI

# Create and start a single event bus that is shared between all modules
bus = EventBus()
bus.start()

# Create and start an instance of driver, passing it the shared event bus
driver = Driver(bus)
driver.start()

# Create the UI backend control interface (publishing control events)
ui_control = ControlUI(bus)

# Create the Pygame UI (subscribes to backend events and renders screens)
ui_display = DisplayUI(bus)
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