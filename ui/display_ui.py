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
import os
import subprocess
from ui.screens.MainScreen import MainScreen
from ui.screens.SettingsScreen import SettingsScreen
from ui.screens.AddScreen import AddScreen
from ui.screens.WiFiScreen import WiFiScreen
from ui.screens.InitScreen import InitScreen
from ui.screens.EmailScreen import EmailScreen

# initialize pygame
pygame.init()

'''
# Moved inside for pathing
def load_devices():
    path = "device_list.json"
    with open(path, "r", encoding='utf-8') as file:
        device_data = json.load(file)
        return list(device_data.values())
'''
    
class DummyScreen:
    """A temporary screen to test the Boot Router"""
    def __init__(self, name):
        self.name = name
    def handle_event(self, event):
        pass
    def update(self):
        pass
    def draw(self, surface):
        surface.fill((0, 0, 0)) # Black background
        font = pygame.font.SysFont(None, 48)
        text = font.render(f"Stub Screen: {self.name}", True, (255, 255, 255))
        surface.blit(text, (100, 100))

class DisplayUI:
    def __init__(self, config, bus=None, ui_control=None):
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

        # For DEV MODE and Pathing
        self.config = config 
        # Load Devices safely using Config Paths
        self.devices = []
        if os.path.exists(self.config.decrypted_list):
            with open(self.config.decrypted_list, "r", encoding='utf-8') as file:
                device_data = json.load(file)
                self.devices = list(device_data.values())

        # Event subscriptions
        self.bus.subscribe("STOP_SYSTEM", self._handle_stop_system)
        self.bus.subscribe("ACK_REMOVE_NODE", self._handle_ack_remove)
        self.bus.subscribe("ACK_POLLING_PAUSED", self._on_ack_polling_paused)
        self.bus.subscribe("DEVICE_LIST_UPDATED", self._handle_device_list_update)
        self.bus.subscribe("Display_token",self._handle_token_display)

        # Establish screen resolution
        self.width = 1024
        self.height = 600

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Zero Monitor LCD UI")

        # Load Devices safely using Dev Mode paths
        self.devices = []
        if os.path.exists(self.config.decrypted_list):
            with open(self.config.decrypted_list, "r", encoding='utf-8') as file:
                device_data = json.load(file)
                self.devices = list(device_data.values())

        # Register screens
        self.screens = {
            "main": MainScreen(self),
            "settings": SettingsScreen (self),
            "add_device": AddScreen(self),

            # Boot Screens
            "init_passcode": InitScreen(self),
            "unlock_vault": InitScreen(self),
            "wifi_setup": WiFiScreen(self),
            "email_setup": EmailScreen(self)
        }

        # Starting on the main screen
        start_key = self._boot_router()
        self.current_screen = self.screens[start_key]
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

    def _on_ack_polling_paused(self, payload):
        name = payload["device"]
        paused = payload["paused"]

        # Update local device list
        for d in self.devices:
            if d["name"] == name:
                d["polling_paused"] = paused

        # If currently in SettingsScreen, rebuild widgets
        if isinstance(self.current_screen, SettingsScreen):
            self.current_screen._build_settings_widgets()


    def _handle_device_list_update(self, devices):
        print("inside _handle_device_list_update")
        self.devices = list(devices.values())
        if isinstance(self.current_screen, MainScreen):
            self.current_screen._build_device_buttons()
    
    def _handle_token_display(self, token):
        """Handles displaying the pairing token in a popup"""
        self.screens["add_device"].token_to_be_disp = True
        self.screens["add_device"].token = token


    def _boot_router(self):
        """Evaluates the system state to determine the first screen to show."""
        print("[UI] Evaluating boot state artifacts...")

        # Step 1: Check Wi-Fi (Local LAN Connection, not Internet)
        try:
            # Asks NetworkManager for the active state of wlan0
            result = subprocess.run(
                ["nmcli", "-t", "-f", "GENERAL.STATE", "dev", "show", "wlan0"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            # nmcli returns "100 (connected)" if it successfully joined a network
            if "100 (connected)" not in result.stdout:
                print("[UI] Boot Router: No local network. Routing to WiFi Setup.")
                return "wifi_setup"
        except Exception as e:
            print(f"[UI] Boot Router: Interface check failed ({e}). Routing to WiFi Setup.")
            return "wifi_setup"

        # Step 2: Check for Encrypted SSH Key
        if not os.path.exists(self.config.ssh_key_enc):
            print("[UI] Boot Router: No secrets found. Routing to Init Screen.")
            return "init_passcode"

        # Step 3: Check for Email Configuration OR Opt-Out
        if not os.path.exists(self.config.email_settings):
            return "email_setup"
        else:
            # Check if they explicitly opted out
            with open(self.config.email_settings, "r") as f:
                data = json.load(f)
                if not data.get("email_configured") and not data.get("email_opt_out"):
                    return "email_setup"
        
        # Standard Boot: Everything is good!
        print("[UI] Boot Router: All artifacts found. Standard Boot.")
        return "unlock_vault" # (This routes to your standard passcode unlock)


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