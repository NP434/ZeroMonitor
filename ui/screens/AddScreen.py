import pygame
from pygame_vkeyboard import *
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.textbox import Textbox
import ui.theme as theme

class AddScreen(BaseScreen):
    """
    Screen for adding new devices to the device list
    """
    def __init__(self, app):
        super().__init__(app)
        self.load_assets

        # Back button
        self.back_button = Button(
            rect=(20, 20, 160, 60),
            text="Back"
        )

        self.DeviceNameBox = Textbox(
            rect=(10, app.height - 30, 100, 50),
            text="Enter Device Name"
        )

        self.keyboard_layout = VKeyboardLayout(VKeyboardLayout.QWERTY,VKeyboardRenderer.DARK)
        self.keyboard = VKeyboard(surface=app,text_consumer=None,
                                  main_layout=self.keyboard_layout
                                 )

    
    def handle_event(self,event):
        self.DeviceNameBox.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.DeviceNameBox.is_clicked(event.pos):
                self.DeviceNameBox.activate((self.keyboard))
        self.keyboard.update([event])

    def draw(self,screen):
        self.DeviceNameBox(screen)
        self.keyboard.draw(screen)



