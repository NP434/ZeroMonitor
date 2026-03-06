import pygame
import ui.theme as theme
import ui.utilities as utilities

class DropDown:
    def __init__(self, app, rect, options, default=None):
        self.app = app
        self.rect = rect
        self.options = options
        self.selected = default if default else options[0]
        self.open = False

        self.option_height = rect.height
        self.font = theme.FONT_MEDIUM

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def handle_event(self, event):
        pos = utilities.get_event_pos(event, self.app)

        if event.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            return

        # Toggle open/close
        if self.is_clicked(pos):
            self.open = not self.open
            return None

        # Handle option clicks
        if self.open:
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + (i + 1) * self.option_height,
                    self.rect.width,
                    self.rect.height
                )
                if opt_rect.collidepoint(pos):
                    self.selected = opt
                    self.open = False
                    return opt

        if self.open:
            self.open = False

        return None
            
    def draw(self, surface):
        pygame.draw.rect(surface, theme.GRAY, self.rect, border_radius=10)
        pygame.draw.rect(surface, theme.WHITE, self.rect, width=2, border_radius=10)

        text = self.font.render(self.selected, True, theme.WHITE)
        surface.blit(text, (self.rect.x + 10, self.rect.y + 10))

        if self.open:
            for i, opt in enumerate(self.options):
                opt_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + (i + 1) * self.option_height,
                    self.rect.width,
                    self.rect.height
                )
                pygame.draw.rect(surface, theme.GRAY, opt_rect)
                pygame.draw.rect(surface, theme.GRAY, opt_rect, width=1)

                t = self.font.render(opt, True, theme.WHITE) 
                surface.blit(t, (opt_rect.x + 10, opt_rect.y + 10))