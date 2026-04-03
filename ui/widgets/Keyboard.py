import pygame
from ui.widgets.Button import Button
import ui.theme as theme

class Keyboard:
    def __init__(self, x, y, width, callback):
        self.x = x
        self.y = y
        self.width = width
        self.callback = callback  # The function to call when a key is pressed
        
        # State: 'lower', 'upper', or 'symbols'
        self.mode = 'lower'
        
        self.layouts = {
            'lower': [
                ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
                ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
                ["Shift", "z", "x", "c", "v", "b", "n", "m", "Back"],
                ["123", "Space", "Enter"]
            ],
            'upper': [
                ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
                ["shift", "Z", "X", "C", "V", "B", "N", "M", "Back"],
                ["123", "Space", "Enter"]
            ],
            'symbols': [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                ["-", "/", ":", ";", "(", ")", "$", "&", "@", "\""],
                ["ABC", ".", ",", "?", "!", "'", "_", "Back"],
                ["ABC", "Space", "Enter"]
            ]
        }
        
        self.buttons = []
        self._build_keys()

    def _build_keys(self):
        """Dynamically generates the button objects based on the current layout"""
        self.buttons.clear()
        
        # Grab the list of keys for the current mode
        current_layout = self.layouts[self.mode]
        
        key_spacing = 8
        row_height = 55
        current_y = self.y
        
        # Base width calculation
        max_keys = 10
        base_key_width = (self.width - (key_spacing * (max_keys - 1))) // max_keys
        
        for row in current_layout:
            # 1. Calculate the EXACT pixel width of this row to center it
            row_pixel_width = 0
            for key_text in row:
                if key_text == 'Space':
                    row_pixel_width += base_key_width * 4
                elif key_text in ['Shift', 'shift', 'Back', 'Enter', '123', 'ABC']:
                    row_pixel_width += int(base_key_width * 1.5)
                else:
                    row_pixel_width += base_key_width
            
            row_pixel_width += key_spacing * (len(row) - 1)
            
            # 2. Center the row
            current_x = self.x + (self.width - row_pixel_width) // 2

            # 3. Build the individual button objects
            for key_text in row:
                actual_width = base_key_width
                display_text = key_text
                
                if key_text == 'Space':
                    actual_width = base_key_width * 4
                    display_text = "SPACE"
                elif key_text in ['Shift', 'shift', 'Back', 'Enter', '123', 'ABC']:
                    actual_width = int(base_key_width * 1.5)

                btn = Button(
                    rect=pygame.Rect(current_x, current_y, actual_width, row_height),
                    text=display_text, 
                    bg_color=theme.DARK_GREY,
                    text_color=theme.WHITE,
                    border_radius=5,
                    border_color=theme.WHITE,
                    border_thickness=2
                )
                self.buttons.append(btn)
                current_x += actual_width + key_spacing
                
            current_y += row_height + key_spacing

    def handle_event(self, pos):
        """Processes clicks and handles mode switching logic (Persistent Shift)"""
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                label = btn.text
                
                # Logic for switching layouts
                if label in ["Shift", "shift"]:
                    self.mode = 'upper' if self.mode == 'lower' else 'lower'
                    self._build_keys() 
                elif label == "123":
                    self.mode = 'symbols'
                    self._build_keys()
                elif label == "ABC":
                    self.mode = 'lower'
                    self._build_keys()
                elif label == "SPACE":
                    self.callback(" ")
                elif label == "Enter":
                    self.callback("Enter")
                elif label == "Back":
                    self.callback("Back")
                else:
                    # Send character to the screen's callback
                    self.callback(label)
                    
                    # --- AUTO-RESET REMOVED ---
                    # We no longer switch back to 'lower' automatically.
                    # The keyboard stays in whatever mode the user selected.
                    
                return True
        return False

    def draw(self, surface):
        for btn in self.buttons:
            btn.draw(surface)