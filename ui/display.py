"""
Filename: display.py
Author: Daniel Stone

File Description: Contains main application and screen manager for Zero Monitor UI. It
initializes pygame, creates window, registers available screens, and handles switching
between them.
"""
import pygame
import sys
from ui.screens import MainScreen, SettingsScreen

# initialize pygame
pygame.init()

class App:
    def __init__(self):
        # Establish screen resolution
        self.width = 1024
        self.height = 600

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Zero Monitor LCD UI")

        # Register screens
        self.screens = {
            "main": MainScreen(self),
            "settings": SettingsScreen (self)
        }

        # Starting on the main screen
        self.current_screen = self.screens["main"]

    def change_screen(self, name):
        self.current_screen = self.screens[name]

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Send events to the active screen to be handled
                self.current_screen.handle_event(event)
            
            # Update and draw the active screen
            self.current_screen.update()
            self.current_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main":
    App().run()