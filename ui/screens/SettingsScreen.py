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

class SettingsScreen(BaseScreen):
    """
    Screen for users to change settings of Zero Monitor device
    """
    def __init__(self, app):
        super().__init__(app)

        # Back button
        self.back_button = Button(
            rect=(20, 20, 160, 60),
            text="Back"
        )

        # Brightness Slider
        self.brightness_slider = Slider(
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
        self.brightness_slider.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.app.change_screen("main")

        self.brightness_slider.handle_event(event)
            

    def draw(self, surface):
        surface.fill(theme.GRAY)

        # Draw back button
        self.back_button.draw(surface)

        # Draw title
        title = theme.DEFAULT_FONT.render("Settings", True, theme.WHITE)
        surface.blit(
            title,
            (self.app.width // 2 - title.get_width() // 2, 100)
        )

        # Draw Brightness slider
        self.brightness_slider.draw(surface)