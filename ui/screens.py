import pygame
import datetime
import ui.theme as theme
from ui.widgets import Button

# Colors
BLACK = (0,0,0)
WHITE = (255, 255, 255)
GRAY = (60, 60, 60)
BLUE = (0, 120, 255)

# Abstract base class for screens

class BaseScreen:
    """
    Abstract Base Class with methods that will be used in all screens
    """
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        """
        Conditions for each event that may happen on the screen
        """
        pass

    def update(self):
        """
        Docstring for update
        """
        pass

    def draw(self, surface):
        """
        Method for drawing elements on the screen.
        """
        pass

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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.settings_button.is_clicked(event.pos):
                self.app.change_screen("settings")
            
            if self.clock_button.is_clicked(event.pos):
                self.use_24hr = not self.use_24hr

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

class SettingsScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)

        # Back button
        self.back_button = Button(
            rect=(20, 20, 160, 60),
            text="Back"
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                self.app.change_screen("main")

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
