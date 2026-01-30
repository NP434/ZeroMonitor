"""
Filename: widgets.py
Author: Daniel Stone
File Description: Classes for different widgets that may be used on screen
"""
import pygame
import ui.theme as theme

# default colors
WHITE = (255, 255, 255)
BLUE = (0, 120, 255)


class Button:
    def __init__(self,
                 rect,
                 text, 
                 font = None, 
                 bg_color = None, 
                 text_color = None, 
                 border_radius = None
    ):
        
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font or theme.DEFAULT_FONT
        self.bg_color = bg_color or theme.BUTTON_BG
        self.text_color = text_color or theme.BUTTON_TEXT
        self.border_radius = border_radius or theme.BUTTON_RADIUS

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center = self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    

class Slider:
    """
    A horizontal slider widget that allows user to drag a handle to select a value
    between min_value and max_value
    """

    def __init__(
            self,
            rect,
            min_value=0,
            max_value=100,
            default_value=50,
            track_color=None,
            handle_color=None,
            on_change=None
    )
        self.rect = pygame.Rect(rect)
        self.min_value = min_value
        self.max_value = max_value
        self.value = default_value

        self.track_color = track_color or theme.GRAY
        self.handle_color = handle_color or theme.WHITE

        # Callback for changes in value
        self.on_change = on_change

        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._handle_rect().collidepoint(event.pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEBUTTONDOWN and self.dragging:
            x = event.pos[0]
            x = max(self.rect.left, min(self.rect.right))
            ratio = (x - self.rect.left) / self.rect.width
            new_value = self.min_value + ratio * (self.max_value - self.min_value)

            if int(new_value) != int(self.value):
                self.value = new_value
                if self.on_change:
                    self.on_change(self.value)

    def draw(self, surface):
        # Draw Track
        pygame.draw.rect(surface, self.track_color, self.rect, border_radius=5)

        # Draw Handle
        handle_rect = self._handle_rect()
        center = handle_rect.center
        radius = handle_rect.width // 2
        pygame.draw.circle(surface, self.handle_color, center, radius)

    def _handle_rect(self):
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        handle_x = self.rect.left + ratio * self.rect.width
        size = 30 # Diameter of handle
        return pygame.Rect(handle_x - size // 2, self.rect.centery - size // 2, size, size)