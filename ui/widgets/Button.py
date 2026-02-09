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

    def _fit_text(self, text, max_width):
        font = self.font
        size = font.size(text)[0]

        # Check if font is a good size
        if size <= max_width:
            return font, text
        
        # Shrink font size until it fits
        font_size = font.get_height()
        while font_size > 8:
            font_size -= 1
            new_font = pygame.font.Font(None, font_size)
            if new_font.size(text)[0] <= max_width:
                return new_font, text
            font = new_font

        # If still too long, truncate with elipses
        elipsis = "..."
        while font.size(text + elipsis)[0] > max_width and len(text) > 0:
            text = text[:-1]

        return font, text + elipsis
        
    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)

        # Fit the text
        max_text_width = self.rect.width - 10
        font_to_use, fitted_text = self._fit_text(self.text, max_text_width)

        text_surf = font_to_use.render(fitted_text, True, self.text_color)
        text_rect = text_surf.get_rect(center = self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)