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
from ui.screens.SystemDashboardScreen import SystemDashboardScreen
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

        # Event subscriptions
        self.bus.subscribe("STOP_SYSTEM", self._handle_stop_system)
        self.bus.subscribe("ACK_REMOVE_NODE", self._handle_ack_remove)
        self.bus.subscribe("ACK_POLLING_PAUSED", self._on_ack_polling_paused)
        self.bus.subscribe("ACK_UPDATE_POLLING_RATE", self._on_ack_update_polling_rate)
        self.bus.subscribe("DEVICE_LIST_UPDATED", self._handle_device_list_update)
        self.bus.subscribe("Display_token",self._handle_token_display)
        self.bus.subscribe("ACK_UPDATE_DEVICE_NAME", self._handle_ack_update_name)

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

        # User Temperature Preference
        self.temp_unit = "C"

        # Register screens
        init_screen = InitScreen(self)
        self.screens = {
            "dashboard": SystemDashboardScreen(self),
            "main": MainScreen(self),
            "settings": SettingsScreen (self),
            "add_device": AddScreen(self),
            "settings" : SettingsScreen(self),
            "init": init_screen,

            # Boot Screens
            "init_passcode": init_screen,
            "wifi_setup": WiFiScreen(self),
            "email_setup": EmailScreen(self)
        }

        # Logic for starting screen, DO NOT CHANGE
        start_key = self._boot_router()
        self.current_screen = self.screens[start_key]
        self._running = False


    def change_screen(self, name):
        self.current_screen = self.screens[name]

    def shutdown(self):
        """UI-initiated shutdown -> publish STOP_SYSTEM"""
        self._running = False
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

    def _on_ack_update_polling_rate(self, payload):
        host = payload["host"]
        rate = payload["poll_rate"]

        if isinstance(self.current_screen, SettingsScreen):
            screen = self.current_screen

            # Commit name change FIRST, before any rebuilds
            if getattr(screen, "pending_name_change", None):
                old_name, new_name = screen.pending_name_change
                screen.pending_polling_change = False
                screen._commit_name_change(old_name, new_name)
                screen.unsaved_changes = False
                return

        # No pending name change — safe to update and rebuild now
        for d in self.devices:
            if d["name"] == host:
                d["polling_frequency"] = rate

        if isinstance(self.current_screen, SettingsScreen):
            screen = self.current_screen
            screen.pending_polling_change = False
            screen.unsaved_changes = False
            screen._build_device_list()
            screen._build_settings_widgets()

        if isinstance(self.current_screen, MainScreen):
            self.current_screen._build_device_buttons()

        main_screen = self.screens.get("main")
        if main_screen and not isinstance(self.current_screen, MainScreen):
            main_screen._build_device_buttons()

    def _handle_ack_update_name(self, payload):
        old_name = payload["old_name"]
        new_name = payload["new_name"]

        # Update local device list
        for d in self.devices:
            if d["name"] == old_name:
                d["name"] = new_name

        # Update current screen if needed
        if isinstance(self.current_screen, SettingsScreen):
            screen = self.current_screen
            if screen.selected_device == old_name:
                screen.selected_device = new_name
            screen._build_device_list()
            screen._build_settings_widgets()

        if isinstance(self.current_screen, MainScreen):
            self.current_screen._build_device_buttons()

        # Also update sidebar data in main screen object if not currently active
        main_screen = self.screens.get("main")
        if main_screen and main_screen is not self.current_screen:
            main_screen._build_device_buttons()
        if isinstance(self.current_screen, SettingsScreen):
            screen = self.current_screen
            if screen.selected_device == old_name:
                screen.selected_device = new_name
            # Update device_buttons
            if old_name in screen.device_buttons:
                screen.device_buttons[new_name] = screen.device_buttons.pop(old_name)


    def _handle_device_list_update(self, devices):
        print("inside _handle_device_list_update")
        self.devices = list(devices.values())

        # Always refresh the main screen model even when it is not active.
        main_screen = self.screens.get("main")
        if main_screen and hasattr(main_screen, "_build_device_buttons"):
            main_screen._build_device_buttons()

        # Keep settings sidebar in sync if settings is active.
        if isinstance(self.current_screen, SettingsScreen):
            if hasattr(self.current_screen, "_build_device_list"):
                self.current_screen._build_device_list()

        # If currently on main, ensure immediate redraw uses refreshed buttons.
        if isinstance(self.current_screen, MainScreen):
            self.current_screen._build_device_buttons()
    
    def _handle_token_display(self, token):
        """Handles displaying the pairing token in a popup"""
        self.screens["add_device"].token_to_be_disp = True
        self.screens["add_device"].token = token


    def _boot_router(self):
        """Evaluates the system state to determine the first screen to show."""
        print("[UI] Evaluating boot state artifacts...")
        
        # 1. Check if the device has an encrypted vault (SSH Key)
        is_first_boot = not os.path.exists(self.config.ssh_key_enc)
        
        # ==========================================
        # STANDARD BOOT (Vault Exists)
        # ==========================================
        if not is_first_boot:
            # Standard Boot: Always authenticate first!
            print("[UI] Vault found. Standard Boot. Routing to Unlock Screen.")
            return "init_passcode"

        # ==========================================
        # FIRST BOOT (No Vault Exists)
        # ==========================================
        print("[UI] First Boot detected. Checking network...")
        
        # Step 1: Check Wi-Fi
        if self.config.dev_mode:
            print("[UI] DEV MODE: Faking network disconnect to test WiFi UI.")
            return "wifi_setup"
        else:
            try:
                # Asks NetworkManager for the active state of wlan0
                result = subprocess.run(
                    ["nmcli", "-t", "-f", "GENERAL.STATE", "dev", "show", "wlan0"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                if "100 (connected)" not in result.stdout:
                    print("[UI] Boot Router: No local network. Routing to WiFi Setup.")
                    return "wifi_setup"
            except Exception as e:
                print(f"[UI] Boot Router: Interface check failed ({e}). Routing to WiFi Setup.")
                return "wifi_setup"

        # Step 2: If Wi-Fi is connected, go straight to Passcode creation
        print("[UI] Network connected. Routing to Passcode Setup.")
        return "init_passcode"


    def run(self):
        self._running = True

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.shutdown()

                # Update activity on touch
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    self.ui_control.update_activity()

                # Send events to the active screen to be handled
                self.current_screen.handle_event(event)
            
            # Update and draw the active screen  
            self.current_screen.update()
            self.current_screen.draw(self.screen)

            # Check for sleep
            self.ui_control.check_sleep()

            # Apply dimming overlay
            alpha = self.ui_control.get_dimming_alpha()
            if alpha > 0:
                overlay = pygame.Surface((self.width, self.height))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(alpha)
                self.screen.blit(overlay, (0, 0))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":  # pragma: no cover
    DisplayUI().run()