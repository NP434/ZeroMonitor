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
        self.device_settings_widgets = []

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

    def _build_settings_buttons(self):
        pass

    def _get_device(self, name):
        for d in self.app.devices:
            if d["name"] == name:
                return d
        return None

    def _build_settings_widgets(self):
        """ Builds device specific widgets when a device is selected """
        self.device_settings_widgets = []

        if not self.selected_device:
            return

        start_x = self.app.width - 250
        start_y = 40
        spacing = 70

        # Build Polling dropdown for each device
        poll_dropdown = DropDown(
            self.app,
            pygame.Rect(start_x, start_y, 200, 40),
            ["Low", "Medium", "High", "Custom"],
            default="Medium" #device.get("poll_rate", "Medium")
        )

        self.device_settings_widgets.append(("poll_rate", poll_dropdown))
        #
        #Add more widgets here later
        #

    def handle_event(self, event):

        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN): 
            return

        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return

        # Device selection on left sidebar
        for name, btn in self.device_buttons.items(): 
            r = btn.rect.move(0, self.scroll_offset) 
            if r.collidepoint(pos): 
                self.selected_device = name 
                self._build_settings_widgets()
                return

        # Settings widgets on the right side
        if self.selected_device:
            result = self.poll_dropdown.handle_event(event)
            for key, widget in self.device_settings_widgets:
                result = widget.handle_event(event)
                if result is not None:
                    device = self._get_device(self.selected_device)
                    device[key] = result

                    # Publish events here


    def draw(self, surface):
        surface.fill(theme.BLACK)

        # Left sidebar background 
        pygame.draw.rect(surface, theme.GRAY, (0, 0, self.sidebar_width, self.app.height))

        # Device buttons
        for name, btn in self.device_buttons.items():
            r = btn.rect.move(0, self.scroll_offset)

            # Highlight selected device
            if name == self.selected_device:
                pygame.draw.rect(surface, theme.YELLOW, r, border_radius=20, width=2)

            btn.draw(surface, override_rect=r)

        # Right side settings panel
        if self.selected_device:
            for key, widget in self.device_settings_widgets:
                widget.draw(surface)
