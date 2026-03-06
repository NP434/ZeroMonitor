import pygame
import sys
import os
import json

# Standard Mock for the Event Bus and Control
from event_bus import EventBus
from ui.control_ui import ControlUI
import ui.theme as theme

# Import the screen you want to test
from ui.screens.InitScreen import InitScreen

class MockDisplayApp:
    def __init__(self):
        pygame.init()
        self.bus = EventBus()
        self.ui_control = ControlUI(self.bus)
        
        # Match display resolution
        self.width = 1024
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        
        # Mock devices for testing
        self.devices = [
            {"name": "LocalNode", "status": "Online", "stats": {"CPU": "20%"}}
        ]
        
        # Screen Management
        self.screens = {}
        self.current_screen = None

    def change_screen(self, name):
        print(f"[TEST] Screen change requested: {name}")
        # In the real app, this switches the object. In test, we just log it.

def run_test():
    app = MockDisplayApp()
    
    # Manually set the screen you are building
    test_screen = InitScreen(app)
    app.current_screen = test_screen

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Pass relevant events to screen
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                app.current_screen.handle_event(event)

        app.current_screen.update()
        app.screen.fill(theme.BLACK) # Clear screen
        app.current_screen.draw(app.screen)
        
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_test()