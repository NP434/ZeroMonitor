"""
Filename: display.py
Author: Daniel Stone

File Description: Contains main application and screen manager for Zero Monitor UI. It
initializes pygame, creates window, registers available screens, and handles switching
between them.
"""
import pygame
import json
import sys
from ui.screens.MainScreen import MainScreen
from ui.screens.SettingsScreen import SettingsScreen

# initialize pygame
pygame.init()

def load_devices():
    path = "device_list.json"
    with open(path, "r", encoding='utf-8') as file:
        device_data = json.load(file)
        return list(device_data.values())
    

class DisplayUI:
    def __init__(self, bus=None, ui_control=None):
        # Initialize an EventBus
        if bus is None:
            from event_bus import EventBus
            bus = EventBus()
            bus.start()
        self.bus = bus

        # Initalize ControlUI
        if ui_control is None:
            from control_ui import ControlUI
            ui_control = ControlUI(self.bus)
        self.ui_control = ui_control

        # Event subscriptions
        self.bus.subscribe("STOP_SYSTEM", self._handle_stop_system)
        self.bus.subscribe("ACK_REMOVE_NODE", self._handle_ack_remove)
        self.bus.subscribe("DEVICE_LIST_UPDATED", self._handle_device_list_update)

        # Establish screen resolution
        self.width = 1024
        self.height = 600

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Zero Monitor LCD UI")

        # Load Devices
        self.devices = load_devices()

        # Register screens
        self.screens = {
            "main": MainScreen(self),
            "settings": SettingsScreen (self)
        }

        # Starting on the main screen
        self.current_screen = self.screens["main"]
        self._running = False


    def change_screen(self, name):
        self.current_screen = self.screens[name]

    def shutdown(self):
        """UI-initiated shutdown -> publish STOP_SYSTEM"""
        self.bus.publish("STOP_SYSTEM", None)

    def _handle_stop_system(self, payload=None):
        """Backend-initiated shutdown -> Shutdown UI Loop"""
        self._running = False

    def _handle_ack_remove(self, payload):
        node = payload.get("node")
        success = payload.get("success")

        print(f"ACK_REMOVE_NODE received for {node}, success={success}")
        
        if isinstance(self.current_screen, MainScreen):
            sel = self.current_screen.selected_device
            if isinstance(sel, dict):
                if sel.get("name") == node:
                    self.current_screen.selected_device = None
            elif sel == node:
                self.current_screen.selected_device = None

            self.current_screen._exit_remove_mode()

    def _handle_device_list_update(self, devices):
        print("inside _handle_device_list_update")
        self.devices = list(devices.values())
        if isinstance(self.current_screen, MainScreen):
            self.current_screen._build_device_buttons()

    def run(self):
        self._running = True

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.shutdown()

                # Send events to the active screen to be handled
                self.current_screen.handle_event(event)
            
            # Update and draw the active screen  
            self.current_screen.update()
            self.current_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    DisplayUI().run()