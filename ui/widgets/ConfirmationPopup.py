import pygame
import ui.theme as theme
import ui.utilities as utilities
from ui.widgets.Button import Button
import ui.utilities as utilities

class ConfirmationPopup:
    def __init__(self, app, message, on_confirm, on_cancel):
        self.app = app
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.open = True

        # Popup geometry
        w = 300
        h = 150
        x = (self.app.width - w) // 2
        y = (self.app.height - h) // 2
        self.rect = pygame.Rect(x, y, w, h)

        # Yes/No button
        self.confirm_yes = Button(
            pygame.Rect(x + 40, y + 90, 80, 40),
            text="Yes",
            bg_color=theme.GREEN
        )

        self.confirm_no = Button(
            pygame.Rect(x + 180, y + 90, 80, 40),
            text="No",
            bg_color=theme.RED
        )

    def handle_event(self, event):
        if not self.open:
            return

        pos = utilities.get_event_pos(event, self.app)
        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):

            if self.confirm_yes.is_clicked(pos):
                self.on_confirm()
                self.open = False
                return
        
            if self.confirm_no.is_clicked(pos):
                self.on_cancel()
                self.open = False
                return

    def draw(self, surface):
        if not self.open:
            return

        # Dim background 
        utilities.dim_background(self.app, surface)

        # Background box
        pygame.draw.rect(surface, theme.GRAY, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme.WHITE, self.rect, width=2, border_radius=10)

        # Text
        msg = theme.DEFAULT_FONT.render(self.message, True, theme.WHITE)
        surface.blit(msg, (self.rect.centerx - msg.get_width() // 2, self.rect.y + 20))

        # Yes/No Buttons
        self.confirm_yes.draw(surface)
        self.confirm_no.draw(surface)
