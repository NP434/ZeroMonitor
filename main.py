# Entry point for the program
import time
from event_bus import EventBus
from driver import Driver
from ui_module import UI

# Create and start a single event bus that is shared between all modules
bus = EventBus()
bus.start()

# Create and start an instance of driver, passing it the shared event bus
driver = Driver(bus)
driver.start()

# Create the UI that will handle event updates and refreshes, will route button presses to "control events"
ui = UI(bus)

# Example commands from the UI, this will be handled by UI_Controller in the future
ui.change_polling_rate("pihole", 30)
ui.add_node()
time.sleep(20)
ui.remove_node()

# Keep alive loop
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    driver.stop_system()