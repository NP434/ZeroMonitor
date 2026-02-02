import pygame
import ui.theme as theme
from ui.widgets.Button import Button

class SidebarPanel:
    def __init__(self, x, y, width_expanded, width_collapsed, height, toggle_button=None):
        self.x = x
        self.y = y
        self.width_collapsed = width_collapsed
        self.width_expanded = width_expanded
        self.current_width = width_collapsed
        self.height = height

        self.expanded = False
        self.animation_speed = 10

        # Colors 
        self.bg_color = (28, 28, 28) 
        self.header_color = (210, 210, 210) 
        self.text_color = (235, 235, 235)

        # Fonts
        self.font_header = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_item = pygame.font.SysFont("Arial", 18)

        # Create Sidebar toggle button
        self.toggle_button = toggle_button or Button(
            rect=(self.x, self.y, self.width_collapsed, 40),
            text="<",
            bg_color=(60, 60, 60),
            text_color=(255, 255, 255),
            font=self.font_header
        )
        self._update_toggle_text()

    def _update_toggle_text(self):
        self.toggle_button.text = "<" if self.expanded else ">"

    def toggle(self):
        self.expanded = not self.expanded
        self._update_toggle_text()

    def update(self):
        """
        Update the width of the sidebar, depending on whether the panel is expanded
        """
        if self.expanded:
            target_width = self.width_expanded
        else:
            target_width = self.width_collapsed

        # Expanding animation
        if self.current_width < target_width:
            if (target_width - self.current_width < self.animation_speed) or (self.current_width > target_width):
                self.current_width = target_width
            else:
                self.current_width += self.animation_speed
        
        if self.current_width > target_width:
            if (self.current_width - target_width < 10) or (self.current_width < target_width):
                self.current_width = target_width
            else:
                self.current_width -= self.animation_speed

        # Move toggle button with sidebar
        self.toggle_button.rect.x = self.x + self.current_width - self.toggle_button.rect.width
        self.toggle_button.rect.y = self.y
        
    def draw(self, surface):
        # Background
        rect = pygame.Rect(self.x, self.y, self.current_width, self.height)
        pygame.draw.rect(surface, self.bg_color, rect)

        # Draw toggle button
        self.toggle_button.draw(surface)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.toggle_button.is_clicked(event.pos):
                self.toggle()

