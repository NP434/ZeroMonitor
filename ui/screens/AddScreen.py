import pygame
from pygame_vkeyboard import *
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.textbox import Textbox
import ui.theme as theme
from ui.widgets.DisplayPopup import DisplayPopup


class AddScreen(BaseScreen):
    """
    Screen for adding new devices to the device list
    """
    def __init__(self, app):
        super().__init__(app)
        self.load_assets()

        # Back button
        self.back_button = Button(
            rect=(0, 0, 100, 60),
            text="Back",
            bg_color=theme.RED
        )
        self.done_button = Button(
            rect=(app.width - 100, 0,100,60),
            text="Done",
            bg_color=theme.GREEN
        )

        self.Endpoint_button = Button(
            rect = (app.width / 4, 100, 100,60),
            text="Endpoint",
            bg_color=theme.BLUE
        )
        self.Password_button = Button(
            rect = ( (3 * app.width / 4 ) , 100, 100,60),
            text="Password Auth",
            bg_color=theme.GRAY
        )
        self.mode = "Endpoint"

        self.UserNameBox = Textbox(
            rect=(382, 200, 300, 50),
            text="Enter User Name",
            title="User Name"
        )
        self.HostNameBox = Textbox(
            rect=(41, 200, 300, 50),
            text="Enter Host Name",
            title="Hostname"
        )
        self.DeviceNameBox = Textbox(
            rect=(711, 200, 300, 50),
            text="Enter Device Name",
            title="Device Name"
        )
        self.passwordBox = Textbox(
            rect=(711, 200, 300, 50),
            text="Enter Device Password",
            title="Password"
        )
        self.keyboard_height=600
        self.keyboard_surface = pygame.Surface((self.app.width, self.keyboard_height))
        self.keyboard_surface.set_colorkey((0, 0, 0))  # optional, for transparency
        self.keyboard_layout = VKeyboardLayout(VKeyboardLayout.QWERTY)
        self.keyboard = VKeyboard(surface=self.keyboard_surface,
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
                                        self.app.height - 600,       # y
                                        self.app.width,              # width
                                        600                          # height
                                        )
        self.popup = None
        self.token_to_be_disp = False
        self.token = None

    def end_token_disp(self):
        self.token_to_be_disp = False
        self.token = None
        self.popup = None

    def update(self):
        if self.active_textbox and self._events:
            self.keyboard.update(self._events)
            self._events.clear()

        if self.token_to_be_disp:
                self.popup = DisplayPopup(
                    app=self.app,
                    message=f"Pairing Token: {self.token}",
                    on_confirm=self.end_token_disp
                )
        if not self.token_to_be_disp:
            self.popup = None
    
    
    def handle_event(self,event):
        self._events.append(event)

        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.FINGERDOWN:
                pos = (
                    int(event.x * self.app.width),
                    int(event.y * self.app.height)
                )
            else: 
                pos = event.pos

            if self.back_button.is_clicked(pos):
                self.app.change_screen("main")
            if self.done_button.is_clicked(pos):
                node_config = {
                "name":self.DeviceNameBox.txt ,
                "hostname": self.HostNameBox.txt,
                "user": self.UserNameBox.txt,
                "operating_system": "OS_Unknown",
                "polling_frequency": 10,
                "pairing_mode" : self.mode,
                "Pword" : None
                }
                if self.mode == "Pass_auth":
                    node_config["Pword"] = self.passwordBox.txt
                self.app.ui_control.add_node(node_config)
            if self.Endpoint_button.is_clicked(pos):
                self.mode = "Endpoint"
                self.Password_button.bg_color = theme.GRAY
                self.Endpoint_button.bg_color = theme.BLUE
            if self.Password_button.is_clicked(pos):
                self.mode = "Pass_auth"
                self.Password_button.bg_color = theme.BLUE
                self.Endpoint_button.bg_color = theme.GRAY
                


            if self.DeviceNameBox.is_clicked(pos):
                if self.mode == "Endpoint":
                    if self.active_textbox is not None:
                        self.active_textbox.activate(False)
                    self.DeviceNameBox.activate(True)
                    self.active_textbox = self.DeviceNameBox
                    self.keyboard.text_consumer = self.DeviceNameBox.consume
                    self.keyboard.set_text("")
                    self.keyboard.enable()
                else:
                    if self.active_textbox is not None:
                        self.active_textbox.activate(False)
                    self.passwordBox.activate(True)
                    self.active_textbox = self.passwordBox
                    self.keyboard.text_consumer = self.passwordBox.consume
                    self.keyboard.set_text("")
                    self.keyboard.enable()

            elif self.UserNameBox.is_clicked(pos):
                if self.active_textbox is not None:
                        self.active_textbox.activate(False)
                self.active_textbox = self.UserNameBox
                self.keyboard.text_consumer = self.UserNameBox.consume
                self.UserNameBox.activate(True)
                self.keyboard.set_text("")  
                self.keyboard.enable()

            elif self.HostNameBox.is_clicked(pos):
                if self.active_textbox is not None:
                        self.active_textbox.activate(False)
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
        #if not self.screen_filled or not self.active_textbox:
        screen.fill(theme.BLACK)


        title = theme.DEFAULT_FONT.render("Add Device", True, theme.WHITE)
        screen.blit(
            title,
            (self.app.width // 2 - title.get_width() // 2, 0)
        )
        self.back_button.draw(screen)
        self.done_button.draw(screen)
        self.Endpoint_button.draw(screen)
        self.Password_button.draw(screen)

        if self.mode == 'Endpoint':
            self.DeviceNameBox.draw(screen)
            self.UserNameBox.draw(screen)
            self.HostNameBox.draw(screen)
        else:
            self.UserNameBox.draw(screen)
            self.HostNameBox.draw(screen)
            self.passwordBox.draw(screen)

        

        if self.active_textbox:
            screen.blit(
            self.keyboard_surface,
            (0, self.app.height - self.keyboard_height)
        )
        self.keyboard.draw()

        #Draw Pairing Token Popup
        if self.token_to_be_disp and self.popup:
            self.popup.draw(screen)