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
        self.load_assets()

        # Back button
        self.back_button = Button(
            rect=(50, 50, 100, 60),
            text="Back",
            bg_color=theme.RED
        )
        self.done_button = Button(
            rect=(app.width - 150, 50,100,60),
            text="Done",
            bg_color=theme.GREEN
        )
        self.DeviceNameBox = Textbox(
            rect=(41, 200, 300, 50),
            text="Enter Device Name"
        )
        self.UserNameBox = Textbox(
            rect=(382, 200, 300, 50),
            text="Enter User Name"
        )
        self.HostNameBox = Textbox(
            rect=(711, 200, 300, 50),
            text="Enter Host Name"
        )
        self.keyboard_layout = VKeyboardLayout(VKeyboardLayout.QWERTY)
        self.keyboard = VKeyboard(surface=app.screen,
                                  text_consumer=None,
                                  main_layout=self.keyboard_layout,
                                  renderer=VKeyboardRenderer.DEFAULT
                                 )
        self.keyboard.disable()
        self._events = []
        self.screen_filled = False
        self.active_textbox = None
        # assuming keyboard uses bottom 250px of the screen
        self.keyboard_rect = pygame.Rect(
                                        0,                           # x
                                        self.app.height - 250,       # y
                                        self.app.width,              # width
                                        250                          # height
                                        )

    def update(self):
        if self.active_textbox and self._events:
            self.keyboard.update(self._events)
            self._events.clear()
    
    
    def handle_event(self,event):
        self._events.append(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            if self.back_button.is_clicked(pos):
                self.app.change_screen("main")
            if self.done_button.is_clicked(pos):
                node_config = {
                "name":self.DeviceNameBox.txt ,
                "hostname": self.HostNameBox.txt,
                "user": self.UserNameBox.txt,
                "operating_system": "OS_Unknown",
                "polling_frequency": 10
                }
                self.app.ui_control.add_node(node_config)
                


            if self.DeviceNameBox.is_clicked(pos):
                self.DeviceNameBox.activate(True)
                self.active_textbox = self.DeviceNameBox
                self.keyboard.text_consumer = self.DeviceNameBox.consume
                self.keyboard.set_text("")
                self.keyboard.enable()

            elif self.UserNameBox.is_clicked(pos):
                self.active_textbox = self.UserNameBox
                self.keyboard.text_consumer = self.UserNameBox.consume
                self.UserNameBox.activate(True)
                self.keyboard.set_text("")  
                self.keyboard.enable()

            elif self.HostNameBox.is_clicked(pos):
                self.HostNameBox.activate(True)
                self.active_textbox = self.HostNameBox
                self.keyboard.text_consumer = self.HostNameBox.consume
                self.keyboard.set_text("")
                self.keyboard.enable()

            elif self.keyboard_rect.collidepoint(pos) and self.active_textbox:
                pass

            else:
                if self.active_textbox:
                    self.active_textbox.activate(False)
                    self.active_textbox = None
                self.keyboard.disable()


    def draw(self,screen):
        if not self.screen_filled or not self.active_textbox:
            screen.fill(theme.GRAY)
            self.screen_filled = True

        title = theme.DEFAULT_FONT.render("Add Device", True, theme.WHITE)
        screen.blit(
            title,
            (self.app.width // 2 - title.get_width() // 2, 100)
        )
        self.back_button.draw(screen)
        self.done_button.draw(screen)

        self.DeviceNameBox.draw(screen)
        self.UserNameBox.draw(screen)
        self.HostNameBox.draw(screen)
  
        self.keyboard.draw()



