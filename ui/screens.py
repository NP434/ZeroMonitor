import pygame
import theme
from widgets import Button

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
        super.__init__(app)
    
        # Create settings button
        self.settings_button = Button(
            rect=(app.width - 180, 20, 160, 60),
            text="Settings"
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.settings_button.is_clicked(event.pos):
                self.app.change_screen("settings")

    def draw(self, surface):
        surface.fill(theme.BLACK)

        # Draw Button
        self.settings_button.draw(surface)

        # Draw remaining contents on screen
        pygame.draw.rect(surface, theme.GRAY, (50, 300, 924, 120))
        text = theme.DEFAULT_FONT.render(
            "Zero Monitor Dashboard",
            True,
            theme.WHITE
        )
        surface.blit(text, (60, 350))

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
