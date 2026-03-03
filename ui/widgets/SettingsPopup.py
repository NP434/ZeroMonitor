"""
Settings Popup to allow users to choose between device and system settings
"""
import pygame
from ui.widgets.Button import Button
import ui.theme as theme
import ui.utilities as utilities

class SettingsPopup:
    def __init__(self, app):
        self.app = app
        self.open = False

        # Popup Geometry
        w = 350
        h = 260
        x = (self.app.width) // 2
        y = (self.app.width) // 2
        self.rect = pygame.Rect(x, y, w, h)

        # Buttons
        self.system_btn = Button(
            pygame.Rect(x + 40, y + 80, w - 80, 50),
            text="System Settings",
            bg_color=theme.BLUE
        )

        self.device_btn = Button(
            pygame.Rect(x + 40, y + 140, w - 80, 50),
            text="Device Settings",
            bg_color=theme.BLUE
        )

        self.cancel_btn = Button(
            pygame.Rect(x + 40, y + 200, w - 80, 50),
            text="Cancel",
            bg_color=theme.RED
        )

    def open_popup(self):
        self.open = True

    def close_popup(self):
        self.open = False

    def handle_event(self, event):
        if not self.open:
            return

        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return

        if self.system_btn.is_clicked(pos):
            self.app.change_screen("systemsettings")
            self.open = False
            return

        if self.device_btn.is_clicked(pos):
            self.app.change_screen("settings") # change to "devicesettings"
            self.open = False
            return

        if self.cancel_btn.is_clicked(pos):
            self.open = False
            return

    def draw(self):
        if not self.open:
            return

        # Draw box

        # Draw buttons

        

        


