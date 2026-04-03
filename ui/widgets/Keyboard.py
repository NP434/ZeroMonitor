import pygame
from ui.widgets.Button import Button
import ui.theme as theme

class Keyboard:
    def __init__(self, x, y, width, callback):
        self.x = x
        self.y = y
        self.width = width
        self.callback = callback  # The function to call when a key is pressed
        
        self.buttons = []
        self.is_shifted = False
        
        # --- UPDATE LAYOUT ARRAYS ---
        self.rows_lower = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'Back'],
            ['-', '_', '.', '@', ' ', 'Enter'] 
        ]
        
        self.rows_upper = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Shift', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'Back'],
            ['-', '_', '.', '@', ' ', 'Enter']
        ]
        
        self._build_keys()

    def _build_keys(self):
        """Dynamically generates the button objects based on the current layout"""
        self.buttons.clear()
        current_layout = self.rows_upper if self.is_shifted else self.rows_lower
        
        key_spacing = 8
        row_height = 55
        current_y = self.y
        
        # Base width is always calculated assuming 10 standard keys fit across the screen
        max_keys = 10
        base_key_width = (self.width - (key_spacing * (max_keys - 1))) // max_keys
        
        for row in current_layout:
            # --- Calculate the EXACT pixel width of this row ---
            row_pixel_width = 0
            for key_text in row:
                if key_text == ' ':
                    row_pixel_width += base_key_width * 4
                elif key_text in ['Shift', 'Back', 'Enter']:
                    row_pixel_width += int(base_key_width * 1.5)
                elif key_text in ['-', '_', '.', '@']:
                    row_pixel_width += int(base_key_width * 1.1)
                else:
                    row_pixel_width += base_key_width
                    
            row_pixel_width += key_spacing * (len(row) - 1)
            
            # --- Center the row perfectly based on its true width ---
            current_x = self.x + (self.width - row_pixel_width) // 2

            # --- Build the buttons ---
            for key_text in row:
                actual_width = base_key_width
                display_text = key_text
                
                if key_text == ' ':
                    actual_width = base_key_width * 4
                    display_text = "SPACE"  # Fix for the weird rectangle!
                elif key_text in ['Shift', 'Back', 'Enter']:
                    actual_width = int(base_key_width * 1.5)
                elif key_text in ['-', '_', '.', '@']:
                    actual_width = int(base_key_width * 1.1)

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
        """Checks if a key was pressed and triggers the callback"""
        for btn in self.buttons:
            if btn.is_clicked(pos):
                if btn.text == "Shift":
                    self.is_shifted = not self.is_shifted
                    self._build_keys() 
                elif btn.text == "SPACE":          
                    self.callback(" ")             # Send a blank space, not the word
                elif btn.text == "Back":           # (Just ensuring Back still works as intended)
                    self.callback("Back")
                elif btn.text == "Enter":
                    self.callback("Enter")
                else:
                    self.callback(btn.text)        # Send the standard letter
                return True
        return False

    def draw(self, surface):
        for btn in self.buttons:
            btn.draw(surface)