import pygame
from widgets import Button

# Colors
BLACK = (0,0,0)
WHITE = (255, 255, 255)
GRAY = (60, 60, 60)
BLUE = (0, 120, 255)

# Abstract base class for screens

class BaseScreen:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

class MainScreen(BaseScreen):
    def __init__(self, app):
        super.__init__(app)
    
    

