"""
Settings Popup to allow users to choose between device and system settings
"""
import pygame
from ui.widgets.Button import Button
import ui.theme as theme
import ui.utilities as utilities

class SettingsPopup:
    def __init__(self, app, anchor_rect):
        self.app = app
        self.open = True

        # Popup Geometry
        w = 350
        h = 190

        # Position under settings button
        x = anchor_rect.x
        y = anchor_rect.bottom + 8

        if x + w > self.app.width:
            x = self.app.width - w - 8

        self.rect = pygame.Rect(x, y, w, h)

        # Buttons
        self.system_btn = Button(
            pygame.Rect(x + 40, y + 10, w - 80, 50),
            text="System Settings",
            bg_color=theme.BLUE
        )

        self.device_btn = Button(
            pygame.Rect(x + 40, y + 70, w - 80, 50),
            text="Device Settings",
            bg_color=theme.BLUE
        )

        self.cancel_btn = Button(
            pygame.Rect(x + 40, y + 130, w - 80, 50),
            text="Cancel",
            bg_color=theme.RED
        )

        self.buttons = [
            self.system_btn,
            self.device_btn,
            self.cancel_btn
        ]

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
            self.app.change_screen("settings")
            self.open = False
            return

        if self.device_btn.is_clicked(pos):
            self.app.change_screen("settings") # change to "devicesettings"
            self.open = False
            return

        if self.cancel_btn.is_clicked(pos):
            self.open = False
            return

    def draw(self, surface):
        if not self.open:
            return

        utilities.dim_background(self.app, surface)

        # Draw box
        pygame.draw.rect(surface, theme.GRAY, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme.WHITE, self.rect, width=2, border_radius=10)

        # Draw buttons
        for btn in self.buttons:
            btn.draw(surface)
