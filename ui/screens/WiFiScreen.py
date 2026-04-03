import pygame
from ui.widgets.Button import Button
from ui.widgets.Keyboard import Keyboard
import ui.theme as theme
import ui.utilities as utilities

class WiFiScreen:
    def __init__(self, app):
        self.app = app
        
        # State variables
        self.ssid = ""
        self.password = ""
        self.active_field = "ssid" # Defaults to typing in the SSID box
        
        # Layout metrics
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 60)
        
        # --- UPDATE WIDGETS TO INCLUDE BORDERS ---
        # The clickable areas for the text boxes remain, but we define their style here.
        self.ssid_rect = pygame.Rect(200, 100, 624, 50)
        self.pass_rect = pygame.Rect(200, 180, 624, 50)
        
        # The Connect Button
        self.connect_btn = Button(
            rect=pygame.Rect(400, 250, 224, 50),
            text="Connect",
            bg_color=theme.GREEN if hasattr(theme, 'GREEN') else (0, 200, 0),
            text_color=theme.WHITE,
            border_radius=5,
            # --- ADD OUTLINE ---
            border_color=theme.WHITE,
            border_thickness=2
        )
        
        # (Keyboard setup is the same)
        self.keyboard = Keyboard(x=50, y=320, width=924, callback=self.on_key_press)

    def on_key_press(self, key):
        """Callback function triggered by the Keyboard widget"""
        # Determine which text variable we are modifying
        current_text = self.ssid if self.active_field == "ssid" else self.password
        
        if key == "Back":
            current_text = current_text[:-1]
        elif key == "Enter":
            self._attempt_connection()
            return
        else:
            current_text += key
            
        # Save the modified text back to the correct variable
        if self.active_field == "ssid":
            self.ssid = current_text
        else:
            self.password = current_text

    def _attempt_connection(self):
        """Called when Connect or Enter is pressed"""
        print(f"[WiFiScreen] Attempting to connect to: {self.ssid}")
        
        # For Dev Mode, we will just simulate a successful connection 
        # and route directly to the next step in the First Boot flow.
        self.app.change_screen("init_passcode")
        
        # FUTURE: You will publish to the event bus here so ControlUI can run nmcli
        # self.app.bus.publish("CONNECT_WIFI", {"ssid": self.ssid, "password": self.password})

    def handle_event(self, event):
        # Use your utility to safely get the position
        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return
            
        # Block double-entries
        if event.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            return
            
        # Process the click
        if self.keyboard.handle_event(pos):
            return 
            
        if self.ssid_rect.collidepoint(pos):
            self.active_field = "ssid"
        elif self.pass_rect.collidepoint(pos):
            self.active_field = "password"
            
        if self.connect_btn.is_clicked(pos):
            self._attempt_connection()

    def update(self):
        pass

    def draw(self, surface):
        surface.fill(theme.BACKGROUND if hasattr(theme, 'BACKGROUND') else (30, 30, 30))
        
        # Draw Title
        title_surf = self.title_font.render("Connect to Wi-Fi", True, theme.WHITE)
        surface.blit(title_surf, (self.app.width//2 - title_surf.get_width()//2, 30))
        
        # --- UPDATE SSID BOX DRAWING ---
        # Make the border color of the input box dynamic based on activity
        ssid_border_color = theme.WHITE if self.active_field == "ssid" else theme.DARK_GREY
        
        # If your Button widget handles drawing rects, you might use it here.
        # Assuming we are drawing the input box as a primitive rect for simplicity:
        pygame.draw.rect(surface, theme.DARK_GREY, self.ssid_rect, border_radius=5) # Background
        pygame.draw.rect(surface, ssid_border_color, self.ssid_rect, width=3, border_radius=5) # Highlight Border
        
        ssid_text = self.font.render(f"SSID: {self.ssid}", True, theme.WHITE)
        surface.blit(ssid_text, (self.ssid_rect.x + 10, self.ssid_rect.y + 10))
        
        # --- UPDATE PASSWORD BOX DRAWING ---
        pass_border_color = theme.WHITE if self.active_field == "password" else theme.DARK_GREY
        
        pygame.draw.rect(surface, theme.DARK_GREY, self.pass_rect, border_radius=5)
        pygame.draw.rect(surface, pass_border_color, self.pass_rect, width=3, border_radius=5)
        
        masked_pass = "*" * len(self.password)
        pass_text = self.font.render(f"Pass: {masked_pass}", True, theme.WHITE)
        surface.blit(pass_text, (self.pass_rect.x + 10, self.pass_rect.y + 10))
        
        # Draw Connect Button
        self.connect_btn.draw(surface)
        
        # Draw Keyboard
        self.keyboard.draw(surface)