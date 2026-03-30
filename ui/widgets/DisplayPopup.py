import pygame
import ui.theme as theme
from ui.widgets.Button import Button

class DisplayPopup:
    def __init__(self, app, message, on_confirm):
        self.app = app
        self.message = message
        self.on_confirm = on_confirm
        self.open = True

        # Popup geometry
        w = 300
        h = 150
        x = (self.app.width - w) // 2
        y = (self.app.height - h ) // 3
        self.rect = pygame.Rect(x, y, w, h)

        # Done button
        self.confirm_done = Button(
            pygame.Rect(x + 110, y + 90, 80, 40),
            text="Done",
            bg_color=theme.BLUE
        )

    def handle_event(self, event):
        if not self.open:
            return

        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            # Determine position based on event type
            if event.type == pygame.FINGERDOWN:
                # Finger coordinates are normalized (0.0 - 1.0)
                pos = (
                    int(event.x * self.app.width),
                    int(event.y * self.app.height)
                )
            else:
                # Mouse event provides pixel coordinates
                pos = event.pos

            if self.confirm_done.is_clicked(pos):
                self.on_confirm()
                self.open = False
                return

    def draw(self, surface):
        if not self.open:
            return

        # Background box
        pygame.draw.rect(surface, theme.GRAY, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme.WHITE, self.rect, width=2, border_radius=10)

        # Text
        msg = theme.DEFAULT_FONT.render(self.message, True, theme.WHITE)
        surface.blit(msg, (self.rect.centerx - msg.get_width() // 2, self.rect.y + 20))

        # Yes/No Buttons
        self.confirm_done.draw(surface)

