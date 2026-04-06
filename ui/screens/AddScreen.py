import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.textbox import Textbox
import ui.theme as theme
from ui.widgets.DisplayPopup import DisplayPopup
from ui.widgets.Keyboard import Keyboard


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
            rect = (app.width / 2 - 100, 125, 100,60),
            text="Endpoint",
            bg_color=theme.BLUE
        )
        self.Password_button = Button(
            rect = ( app.width / 2, 125, 100,60),
            text="Password",
            bg_color=theme.GRAY
        )
        self.mode = "Endpoint"

        self.UserNameBox = Textbox(
            rect=(382, 225, 300, 50),
            text="Enter User Name",
            title="User Name"
        )
        self.HostNameBox = Textbox(
            rect=(41, 225, 300, 50),
            text="Enter Host Name",
            title="Hostname"
        )
        self.DeviceNameBox = Textbox(
            rect=(711, 225, 300, 50),
            text="Enter Device Name",
            title="Device Name"
        )
        self.passwordBox = Textbox(
            rect=(711, 225, 300, 50),
            text="Enter Device Password",
            title="Password"
        )
        self.keyboard_height = 300

        self.keyboard = Keyboard(
            x=0,
            y=self.app.height - self.keyboard_height,
            width=self.app.width,
            callback=self._on_key_pressed
        )
        self._events = []
        self.screen_filled = False
        self.active_textbox = None
        # assuming keyboard uses bottom 250px of the screen
        self.popup = None
        self.token_to_be_disp = False
        self.token = None

    def end_token_disp(self):
        self.token_to_be_disp = False
        self.token = None
        self.popup = None

        if self.token_to_be_disp:
                self.popup = DisplayPopup(
                    app=self.app,
                    message=f"Pairing Token: {self.token}",
                    on_confirm=self.end_token_disp
                )
        if not self.token_to_be_disp:
            self.popup = None
    
    def _on_key_pressed(self, key):
        if not self.active_textbox:
            return

        if key == "Back":
            self.active_textbox.txt = self.active_textbox.txt[:-1]

        elif key == "Enter":
            self.active_textbox.activate(False)
            self.active_textbox = None

        else:
            self.active_textbox.txt += key
    
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
                self.active_textbox = None
                self.popup = None
                self.token_to_be_disp = None
                self.DeviceNameBox.txt = ""
                self.HostNameBox.txt = ""
                self.UserNameBox.txt = ""
                self.Password_button.txt = ""
        
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
                    
                else:
                    if self.active_textbox is not None:
                        self.active_textbox.activate(False)
                    self.passwordBox.activate(True)
                    self.active_textbox = self.passwordBox
                    self.keyboard.text_consumer = self.passwordBox.consume
                    

            elif self.UserNameBox.is_clicked(pos):
                if self.active_textbox is not None:
                        self.active_textbox.activate(False)
                self.active_textbox = self.UserNameBox
                self.keyboard.text_consumer = self.UserNameBox.consume
                self.UserNameBox.activate(True)
                

            elif self.HostNameBox.is_clicked(pos):
                if self.active_textbox is not None:
                        self.active_textbox.activate(False)
                self.HostNameBox.activate(True)
                self.active_textbox = self.HostNameBox
                self.keyboard.text_consumer = self.HostNameBox.consume
                

            elif self.active_textbox:
                if self.keyboard.handle_event(pos):
                    return

            else:
                if self.active_textbox:
                    self.active_textbox.activate(False)
                    self.active_textbox = None

                
            if self.token_to_be_disp:
                self.popup = DisplayPopup(
                    app=self.app,
                    message=f"Pairing Token: {self.token}",
                    on_confirm=self.end_token_disp
                )
                


    def draw(self,screen):
        #if not self.screen_filled or not self.active_textbox:
        screen.fill(theme.BLACK)

        top_bar_height = 90
        pygame.draw.rect(screen, theme.DARK_GRAY, (0, 0, self.app.width, 70))
        pygame.draw.line(screen, theme.BLUE, (0, 70), (self.app.width, 70), 2)
        title = theme.DEFAULT_FONT.render("Add Device", True, theme.BRIGHT_BLUE)
        screen.blit(
            title,
            (self.app.width // 2 - title.get_width() // 2, 0)
        )
        self.back_button.draw(screen)
        self.done_button.draw(screen)
        self.Endpoint_button.draw(screen)
        self.Password_button.draw(screen)
        
        mode = theme.DEFAULT_FONT.render("Pairing Mode", True, theme.WHITE)
        screen.blit(mode, (self.app.width / 2 - mode.get_width() / 2, 80))

        if self.mode == 'Endpoint':
            self.DeviceNameBox.draw(screen)
            self.UserNameBox.draw(screen)
            self.HostNameBox.draw(screen)
        else:
            self.UserNameBox.draw(screen)
            self.HostNameBox.draw(screen)
            self.passwordBox.draw(screen)

        

        if self.active_textbox:
            self.keyboard.draw(screen)

        #Draw Pairing Token Popup
        if self.token_to_be_disp and self.popup:
            self.popup.draw(screen)