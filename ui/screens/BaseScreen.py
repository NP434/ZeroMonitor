import pygame
import os

class BaseScreen:
    """
    Abstract Base Class with methods that will be used in all screens
    """
    def __init__(self, app):
        self.app = app
        self.assets = {}

    def load_assets(self):
        """
        Loads all PNG assets for this screen into self.assets.
        Folder is based on screen class name
        """
        screen_name = self.__class__.__name__.replace("Screen", "").lower()
        folder = os.path.join("assets", screen_name)

        if not os.path.isdir(folder):
            return
        
        for filename in os.listdir(folder):
            if filename.lower().endswith(".png"):
                path = os.path.join(folder, filename)
                image = pygame.image.load(path).convert_alpha()
                self.assets[filename] = image

    def handle_event(self, event):
        """
        Conditions for each event that may happen on the screen
        """
        pass

    def update(self):
        """
        Docstring for update
        """
        pass

    def draw(self, surface):
        """
        Method for drawing elements on the screen.
        """
        pass

