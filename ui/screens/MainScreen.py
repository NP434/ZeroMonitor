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