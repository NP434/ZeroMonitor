import pygame
from ui.widgets.Button import Button
from ui.screens.BaseScreen import BaseScreen
import ui.theme as theme
import ui.utilities as utilities

class InitScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app) 

        # Store User Entered Passcode
        self.passcode = ""

        # Keypad Grid
        self.buttons = []
        self._setup_keypad()
    
    def _setup_keypad(self):
        # Circle Button Settings
        btn_size = 80
        spacing_x, spacing_y = 30, 20
        radius = btn_size // 2 

        # Center of grid
        total_grid_width = (3 * btn_size) + (2 * spacing_x)
        start_x = (self.app.width - total_grid_width) // 2
        start_y = 180

        # Create 1-9 in a 3x3 grid
        for i in range(9):
            row, col = divmod(i, 3) # row is 0-2, col is 0-2
            x = start_x + col * (btn_size + spacing_x)
            y = start_y + row * (btn_size + spacing_y)
            
            self.buttons.append(Button(
                rect=pygame.Rect(x, y, btn_size, btn_size),
                text=str(i + 1),
                bg_color=theme.BLUE,
                text_color=theme.WHITE,
                border_radius=radius # This creates the circle effect
            ))

        # Add the "0" button centered at the bottom
        zero_x = start_x + (btn_size + spacing_x) # Middle column
        zero_y = start_y + 3 * (btn_size + spacing_y) # Fourth row
        
        self.buttons.append(Button(
            rect=pygame.Rect(zero_x, zero_y, btn_size, btn_size),
            text="0",
            bg_color=theme.BLUE,
            text_color=theme.WHITE,
            border_radius=radius
        ))

    def handle_event(self, event):
        # Need to get position from utility
        pos = utilities.get_event_pos(event, self.app)

        # if pos is None, exit
        if pos is None:
            return

        # Check every button in list
        for btn in self.buttons:
            if btn.is_clicked(pos):
                # Add the number to the passcode
                if len(self.passcode) < 8:
                    self.passcode += btn.text
                    print(f"Entry: {self.passcode}")
                
                # Max digit logic
                if len(self.passcode) == 8:
                    print(f"Entered 8 Digits: {self.passcode}")
                    #self.app.change_screen("main")

    def draw(self, surface):
        surface.fill(theme.BLACK) 

        # Draw Title
        title = theme.DEFAULT_FONT.render("Enter Passcode", True, theme.WHITE)
        surface.blit(title, (self.app.width // 2 - title.get_width() // 2, 60))

        # Draw Passcode Dots (iphone style)
        dot_spacing = 30
        num_dots = 8
        total_width = (num_dots - 1) * dot_spacing
        start_x = (self.app.width // 2) - (total_width // 2)

        for i in range(num_dots):
            x = start_x + (i * dot_spacing)
            color = theme.YELLOW if i < len(self.passcode) else (50, 50, 50)
            pygame.draw.circle(surface, color, (x, 120), 8)

        # Draw all the circular buttons
        for btn in self.buttons:
            btn.draw(surface)