import pygame
import subprocess
from pygame_vkeyboard import *
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.textbox import Textbox
import ui.theme as theme
import ui.utilities as utilities

class WiFiScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        
        # Standard Buttons
        self.back_button = Button(
            rect=(0, 0, 100, 60),
            text="Back",
            bg_color=theme.RED
        )
        self.join_button = Button(
            rect=(self.app.width - 100, 0, 100, 60),
            text="Join",
            bg_color=theme.GREEN
        )

        # Textboxes
        self.SSIDBox = Textbox(
            rect=(self.app.width // 2 - 150, 100, 300, 50),
            text="Enter SSID",
            title="Network Name"
        )
        self.PasswordBox = Textbox(
            rect=(self.app.width // 2 - 150, 180, 300, 50),
            text="Enter Password",
            title="WiFi Password"
        )

        # Keyboard Setup from Noah
        self.keyboard_height = 600
        self.keyboard_surface = pygame.Surface((self.app.width, self.keyboard_height))
        self.keyboard_surface.set_colorkey((0, 0, 0))
        self.keyboard_layout = VKeyboardLayout(VKeyboardLayout.QWERTY)
        self.keyboard = VKeyboard(
            surface=self.keyboard_surface,
            text_consumer=None,
            main_layout=self.keyboard_layout,
            renderer=VKeyboardRenderer.DEFAULT
        )
        self.keyboard.disable()
        
        self.keyboard_rect = pygame.Rect(
            0,
            self.app.height - 600,
            self.app.width,
            600
        )

        # State Management
        self._events = []
        self.active_textbox = None
        self.status_msg = "Connect to WiFi"

    def update(self):
        """Processes the event queue for the keyboard"""
        if self.active_textbox and self._events:
            self.keyboard.update(self._events)
            self._events.clear()

    def handle_event(self, event):
        # Capture all events into the queue
        self._events.append(event)

        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.FINGERDOWN:
                pos = (int(event.x * self.app.width), int(event.y * self.app.height))
            else:
                pos = event.pos

            # UI Buttons
            if self.back_button.is_clicked(pos):
                self.app.change_screen("main")
            
            if self.join_button.is_clicked(pos):
                self.attempt_connection()

            if self.SSIDBox.is_clicked(pos):
                if self.active_textbox is not None:
                    self.active_textbox.activate(False)
                self.SSIDBox.activate(True)
                self.active_textbox = self.SSIDBox
                self.keyboard.text_consumer = self.SSIDBox.consume
                self.keyboard.set_text("")
                self.keyboard.enable()

            elif self.PasswordBox.is_clicked(pos):
                if self.active_textbox is not None:
                    self.active_textbox.activate(False)
                self.PasswordBox.activate(True)
                self.active_textbox = self.PasswordBox
                self.keyboard.text_consumer = self.PasswordBox.consume
                self.keyboard.set_text("")
                self.keyboard.enable()

            elif self.keyboard_rect.collidepoint(pos) and self.active_textbox:
                pass

            else:
                if self.active_textbox:
                    self.active_textbox.activate(False)
                    self.active_textbox = None
                self.keyboard.disable()

    def attempt_connection(self):
        self.status_msg = "Attempting Connection..."
        cmd = ["nmcli", "device", "wifi", "connect", self.SSIDBox.txt, "password", self.PasswordBox.txt]
        
        try:
            # nmcli
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                self.app.change_screen("init")
            else:
                self.status_msg = "Connection Failed"
        except:
            self.status_msg = "System Timeout"

    def draw(self, screen):
        screen.fill(theme.BLACK)

        # Title
        title = theme.DEFAULT_FONT.render("WiFi Setup", True, theme.WHITE)
        screen.blit(title, (self.app.width // 2 - title.get_width() // 2, 10))

        # Status
        status_surf = theme.SMALL_FONT.render(self.status_msg, True, theme.RED)
        screen.blit(status_surf, (self.app.width // 2 - status_surf.get_width() // 2, 65))

        # Widgets
        self.back_button.draw(screen)
        self.join_button.draw(screen)
        self.SSIDBox.draw(screen)
        self.PasswordBox.draw(screen)

        # Keyboard Rendering
        if self.active_textbox:
            screen.blit(
                self.keyboard_surface,
                (0, self.app.height - self.keyboard_height)
            )
            self.keyboard.draw()