"""
Filename: SettingsScreen.py
Author: Daniel Stone

File Description: Settings Screen module using widgets
"""
import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.Slider import Slider
import ui.theme as theme
import ui.utilities as utilities

class SystemSettingsScreen(BaseScreen):
    """
    Screen for users to change settings of Zero Monitor device
    """
    def __init__(self, app):
        super().__init__(app)
        self.load_assets()

        self.load_assets()
        house_icon = pygame.transform.smoothscale(self.assets["house.png"], (30,30))
        settings_icon = pygame.transform.smoothscale(self.assets["settings.png"], (30,30))

        # Navigation buttons
        self.home_btn = Button(
            pygame.Rect(20, 20, 50, 50),
            image=house_icon,
            bg_color=theme.BLUE,
            border_radius=10
        )

        self.device_btn = Button(
            pygame.Rect(80, 20, 50, 50),
            image=settings_icon,
            bg_color=theme.YELLOW,
            border_radius=10
        )

        # Brightness Slider
        self.brightness_slider = Slider(
            self.app,
            rect=(200, 200, 600, 20),
            min_value=0,
            max_value=100,
            default_value=50,
            label="Brightness",
            track_color=theme.BLUE,
            on_change=self.on_brightness_change
        )

        self.brightness_value = 50

    def on_brightness_change(self, value):
        pass

    def handle_event(self, event):

        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if self.home_btn.is_clicked(pos):
                self.app.change_screen("main")
                return

            if self.device_btn.is_clicked(pos):
                self.app.change_screen("devicesettings")
                return

        self.brightness_slider.handle_event(event)

    def draw(self, surface):
        surface.fill(theme.GRAY)

        # Draw navigation buttons
        self.home_btn.draw(surface)
        self.device_btn.draw(surface)

        # Draw title
        title = theme.DEFAULT_FONT.render("Settings", True, theme.WHITE)
        surface.blit(
            title,
            (self.app.width // 2 - title.get_width() // 2, 100)
        )

        # Draw Brightness slider
        self.brightness_slider.draw(surface)