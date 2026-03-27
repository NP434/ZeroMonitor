import pygame
import ui.theme as theme


class ToggleSwitch:
    """
    A simple ON/OFF toggle switch widget.
    - rect: (x, y, width, height)
    - default: initial boolean value
    - on_change: optional callback when toggled
    """

    def __init__(self, app, rect, default=False, on_change=None):
        self.app = app
        self.rect = pygame.Rect(rect)
        self.value = default
        self.on_change = on_change

        # Animation state
        self.anim_progress = 1.0 if self.value else 0.0
        self.anim_speed = 0.15  # lower = slower animation

    def handle_event(self, event):
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            return None

        # Normalize touch/mouse position
        if event.type == pygame.FINGERDOWN:
            pos = (int(event.x * self.app.width), int(event.y * self.app.height))
        else:
            pos = event.pos

        if self.rect.collidepoint(pos):
            self.value = not self.value
            if self.on_change:
                self.on_change(self.value)
            return self.value

        return None

    def update(self):
        """Smooth animation toward target state."""
        target = 1.0 if self.value else 0.0
        self.anim_progress += (target - self.anim_progress) * self.anim_speed

    def draw(self, surface):
        self.update()

        # Colors
        bg_on = theme.GREEN
        bg_off = theme.DARK_GRAY
        knob_color = theme.WHITE

        # Background track
        pygame.draw.rect(
            surface,
            bg_on if self.value else bg_off,
            self.rect,
            border_radius=self.rect.height // 2
        )

        # Knob position
        knob_diameter = self.rect.height - 6
        knob_x = self.rect.x + 3 + (self.rect.width - knob_diameter - 6) * self.anim_progress
        knob_y = self.rect.y + 3

        pygame.draw.ellipse(
            surface,
            knob_color,
            (knob_x, knob_y, knob_diameter, knob_diameter)
        )
