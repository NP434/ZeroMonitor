import pygame
import ui.theme as theme

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
            label="",
            track_color=None,
            handle_color=None,
            text_color=None,
            on_change=None
        ):
        self.rect = pygame.Rect(rect)
        self.min_value = min_value
        self.max_value = max_value
        self.value = default_value

        self.label = label

        self.track_color = track_color or theme.GRAY
        self.handle_color = handle_color or theme.WHITE
        self.text_color = text_color or theme.WHITE

        # Callback for changes in value
        self.on_change = on_change

        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._handle_rect().collidepoint(event.pos):
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            x = event.pos[0]
            x = max(self.rect.left, min(event.pos[0], self.rect.right))
            ratio = (x - self.rect.left) / self.rect.width
            new_value = self.min_value + ratio * (self.max_value - self.min_value)

            if int(new_value) != int(self.value):
                self.value = new_value
                if self.on_change:
                    self.on_change(self.value)

    def draw(self, surface):
        # Draw Label
        if self.label:
            label_text = theme.DEFAULT_FONT.render(self.label, True, self.text_color)
            surface.blit(label_text, (self.rect.left, self.rect.top - 30))

        # Draw Value
        value_text = theme.DEFAULT_FONT.render(str(int(self.value)), True, self.text_color)
        surface.blit(value_text, (self.rect.right + 15, self.rect.centery - 10))

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