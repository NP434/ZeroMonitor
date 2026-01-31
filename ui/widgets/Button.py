import pygame
import ui.theme as theme

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