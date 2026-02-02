import datetime
import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
from ui.widgets.SidebarPanel import SidebarPanel
import ui.theme as theme

class MainScreen(BaseScreen):
    """
    Dashboard/main screen that users will see
    """
    def __init__(self, app):
        super().__init__(app)
    
        # Create settings button
        self.settings_button = Button(
            rect=(app.width - 180, 20, 160, 60),
            text="Settings"
        )

        self.clock_button = Button(
            rect=(20, 20, 150, 40),
            text="",
            bg_color=None,
            border_radius=0
        )
        self.use_24hr = False

        self.sidebar = SidebarPanel(
            x=0,
            y=0,
            width_expanded=250,
            width_collapsed=40,
            height=app.height
        )

        self.device_buttons = []
        self.device_scroll = 0

        self._build_device_buttons()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.settings_button.is_clicked(event.pos):
                self.app.change_screen("settings")
            
            if self.clock_button.is_clicked(event.pos):
                self.use_24hr = not self.use_24hr

        self.sidebar.handle_event(event)

    def update(self):
        self.sidebar.update()

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # --- Top Bar Elements ---

        # Time (topleft)
        if self.use_24hr:
            now = datetime.datetime.now().strftime("%H:%M")
        else:
            now = datetime.datetime.now().strftime("%I:%M %p")

        time_text = theme.DEFAULT_FONT.render(now, True, theme.WHITE)
        surface.blit(time_text, (20, 20))

        # Title Centered Horizontally
        title_text = theme.DEFAULT_FONT.render("Zero Monitor Dashboard", True, theme.WHITE)
        title_rect = title_text.get_rect(
            center=(self.app.width // 2, 50)
        )
        surface.blit(title_text, title_rect)

        # Draw Button
        self.settings_button.draw(surface)

        # Draw remaining contents on screen
        pygame.draw.rect(surface, theme.GRAY, (50, 150, 924, 120))
        text = theme.DEFAULT_FONT.render(
            "System stats here...",
            True,
            theme.WHITE
        )
        surface.blit(text, (60, 200))

        # Draw sidebar
        self.sidebar.draw(surface)

    def _build_device_buttons(self):
        button_width = self.sidebar.width_expanded - 20
        button_height = 40
        x = self.sidebar.x + 10
        y = 60

        for device in self.app.devices:
            status = device.get("status", "Offline")
            color = theme.STATUS_COLORS.get(status, (100, 100, 100))

            btn = Button(
                rect=(x, y, button_width, button_height),
                text=device["name"],
                bg_color=color
            )
            btn.device = device
            self.device_buttons.append(btn)

            y += button_height + 10