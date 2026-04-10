import pygame
from ui.screens.BaseScreen import BaseScreen
from ui.widgets.Button import Button
import ui.theme as theme
import ui.utilities as utilities

class UpdateScreen(BaseScreen):
    def __init__(self, app):
        super().__init__(app)
        self.status_text = "Checking for updates..."
        self.update_available = False
        self.is_checking = True
        
        # Subscribe to the backend
        self.app.bus.subscribe("UPDATE_STATUS", self._on_update_status)
        
        # Buttons 
        self.btn_yes = Button(rect=pygame.Rect(200, 300, 150, 60), text="Update Now", bg_color=theme.GREEN)
        self.btn_no = Button(rect=pygame.Rect(450, 300, 150, 60), text="Skip", bg_color=theme.RED)

    def on_enter(self):
        """Fires when the screen loads."""
        self.is_checking = True
        self.update_available = False
        self.status_text = "Checking for updates..."
        
        # Tell the backend to check for update
        self.app.bus.publish("CHECK_FOR_UPDATE", {})

    def _on_update_status(self, data):
        """Callback when the UpdateManager finishes checking or fails."""
        status = data.get("status")
        
        if status == "available":
            self.update_available = True
            self.is_checking = False
            self.status_text = "A new update is available! Install now?"
        
        elif status in ["up_to_date", "error"]:
            # If there's no update, or the check failed (no internet), just move on quietly
            self.app.change_screen("init_passcode")
            
        elif status == "update_failed":
            self.status_text = "Update failed. Skipping..."
            # Wait a moment for them to read it, then move on
            self.app.change_screen("init_passcode")

    def handle_event(self, event):
        # Guard clause: Do nothing if we are waiting on the backend
        if self.is_checking or not self.update_available:
            return 

        pos = utilities.get_event_pos(event, self.app)
        
        # If pos is None (e.g., it wasn't a click/touch event), exit early
        if pos is None:
            return
        
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if self.btn_yes.is_clicked(pos):
                self.is_checking = True 
                self.status_text = "Installing update... Please wait."
                self.app.bus.publish("APPLY_UPDATE", {})
                
            elif self.btn_no.is_clicked(pos):
                self.app.change_screen("init_passcode")

    def draw(self, surface):
        surface.fill(theme.BLACK)
        
        text_surf = theme.FONT_MEDIUM.render(self.status_text, True, theme.WHITE)
        surface.blit(text_surf, (self.app.width // 2 - text_surf.get_width() // 2, 150))

        if not self.is_checking and self.update_available:
            self.btn_yes.draw(surface)
            self.btn_no.draw(surface)