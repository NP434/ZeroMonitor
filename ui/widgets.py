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
        