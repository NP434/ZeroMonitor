import pygame
import json
import os
import ui.utilities as utilities
from ui.widgets.Button import Button
from ui.widgets.Keyboard import Keyboard
import ui.theme as theme

class EmailScreen:
    def __init__(self, app):
        self.app = app
        
        # State variables
        self.email = ""
        
        # Layout metrics
        self.font = pygame.font.SysFont(None, 40)
        self.title_font = pygame.font.SysFont(None, 60)
        self.subtitle_font = pygame.font.SysFont(None, 30)
        
        # The single input box
        self.email_rect = pygame.Rect(200, 130, 624, 50)
        
        # Action Buttons
        self.save_btn = Button(
            rect=pygame.Rect(200, 220, 280, 50),
            text="Save & Continue",
            bg_color=theme.GREEN if hasattr(theme, 'GREEN') else (0, 200, 0),
            text_color=theme.WHITE,
            border_radius=5,
            border_color=theme.WHITE,
            border_thickness=2
        )
        
        self.skip_btn = Button(
            rect=pygame.Rect(544, 220, 280, 50),
            text="Skip Alerts",
            bg_color=theme.DARK_GREY,
            text_color=theme.WHITE,
            border_radius=5,
            border_color=theme.WHITE,
            border_thickness=2
        )
        
        # Initialize the Custom Keyboard
        self.keyboard = Keyboard(x=50, y=320, width=924, callback=self.on_key_press)

    def on_key_press(self, key):
        if key == "Back":
            self.email = self.email[:-1]
        elif key == "Enter":
            self._save_settings(opt_out=False)
        else:
            self.email += key

    def _save_settings(self, opt_out=False):
        """Saves the email preference to the temp JSON and advances the screen"""
        # If they hit save but didn't type anything, treat it like a skip
        if not opt_out and self.email.strip() == "":
            opt_out = True
            
        email_data = {
            "email_configured": not opt_out,
            "email_address": self.email if not opt_out else "",
            "email_opt_out": opt_out
        }
        
        # Save to the temp file path established in paths.py
        try:
            with open(self.app.config.email_settings, "w") as f:
                json.dump(email_data, f, indent=4)
            print(f"[EmailScreen] Settings saved. Opt-out: {opt_out}")
        except Exception as e:
            print(f"[EmailScreen] Error saving email settings: {e}")
            
        # Route to the Add Device screen!
        self.app.change_screen("add_device")

    def handle_event(self, event):
        pos = utilities.get_event_pos(event, self.app)
        if pos is None:
            return
            
        if event.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            return
            
        # 1. Check Keyboard
        if self.keyboard.handle_event(pos):
            return 
                
        # 2. Check Action Buttons
        if self.save_btn.is_clicked(pos):
            self._save_settings(opt_out=False)
        elif self.skip_btn.is_clicked(pos):
            self._save_settings(opt_out=True)

    def update(self):
        pass

    def draw(self, surface):
        surface.fill(theme.BACKGROUND if hasattr(theme, 'BACKGROUND') else (30, 30, 30))
        
        # Draw Titles
        title_surf = self.title_font.render("Set Up Node Alerts", True, theme.WHITE)
        surface.blit(title_surf, (self.app.width//2 - title_surf.get_width()//2, 20))
        
        sub_surf = self.subtitle_font.render("Enter an email to receive alerts when a monitored device goes offline.", True, theme.WHITE)
        surface.blit(sub_surf, (self.app.width//2 - sub_surf.get_width()//2, 80))
        
        # Draw Email Box (Always active since it's the only box)
        pygame.draw.rect(surface, theme.DARK_GREY, self.email_rect, border_radius=5)
        pygame.draw.rect(surface, theme.WHITE, self.email_rect, width=3, border_radius=5)
        
        email_text = self.font.render(f"Email: {self.email}", True, theme.WHITE)
        surface.blit(email_text, (self.email_rect.x + 10, self.email_rect.y + 10))
        
        # Draw Buttons & Keyboard
        self.save_btn.draw(surface)
        self.skip_btn.draw(surface)
        self.keyboard.draw(surface)