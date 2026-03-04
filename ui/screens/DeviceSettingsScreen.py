"""
Screen for settings relating specifically to the devices that are paired
"""
import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
import ui.theme as theme
import ui.utilities as utilities
from ui.widgets.Dropdown import DropDown
from ui.widgets.ConfirmationPopup import ConfirmationPopup

class DeviceSettingsScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)

        self.sidebar_width = 260
        self.scroll_offset = 0

        self.selected_device = None
        self.device_buttons = {}
        self.poll_dropdown = None

        self._build_device_list()

    def _build_device_list(self):
        self.device_buttons.clear()
        
        x = 10
        y = 20
        w = self.sidebar_width - 20
        h = 60

        for device in self.app.devices:
            name = device["name"]
            rect = pygame.Rect(x, y, w, h)

            self.device_buttons[name] = Button(
                rect,
                text=name,
                bg_color=None,
                text_color=theme.WHITE,
                border_radius=10,
                align="left"
            )

            y += h + 10

    def handle_event(self, event):
        pass

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # Left sidebar background 
        pygame.draw.rect(surface, theme.GRAY, (0, 0, self.sidebar_width, self.app.height))

        # Device buttons
        for name, btn in self.device_buttons.items():
            r = btn.rect.move(0, self.scroll_offset)

            # Highlight selected device
            if name == self.selected_device:
                pygame.draw.rect(surface, theme.YELLOW, r, border_radius=10)

            btn.draw(surface)

    def _build_settings_buttons():
        pass
