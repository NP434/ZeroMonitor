import pygame
from ui.widgets.Button import Button
import ui.theme as theme

class Numpad:
    def __init__(self, x, y, callback):
        """
        x, y      → top-left corner of the numpad
        callback  → function called with each key press ("0"-"9", "DEL", "OK")
        """
        self.x = x
        self.y = y
        self.callback = callback
        self.buttons = []
        self._build_keys()

    def _build_keys(self):
        """Creates a 3x4 numeric keypad layout"""
        self.buttons.clear()

        layout = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["DEL", "0", "OK"]
        ]

        key_w = 70
        key_h = 60
        spacing = 10

        current_y = self.y

        for row in layout:
            current_x = self.x
            for label in row:
                btn = Button(
                    rect=pygame.Rect(current_x, current_y, key_w, key_h),
                    text=label,
                    bg_color=theme.DARK_GRAY,
                    text_color=theme.WHITE,
                    border_radius=8,
                    border_color=theme.WHITE,
                    border_thickness=2
                )
                self.buttons.append(btn)
                current_x += key_w + spacing

            current_y += key_h + spacing

    def handle_event(self, pos):
        """Returns True if a button was pressed"""
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                label = btn.text
                self.callback(label)
                return True
        return False

    def draw(self, surface):
        for btn in self.buttons:
            btn.draw(surface)
