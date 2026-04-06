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
        Loads PNG assets into self.assets.
        Global assets are in /assets
        Screen-specific assets are in /assets/<screen>
        """
        self.assets = {}

        screen_name = self.__class__.__name__.replace("Screen", "").lower()
        screen_folder = os.path.join("assets", screen_name)

        # Load global assets first
        if os.path.isdir("assets"):
            for filename in os.listdir("assets"):
                path = os.path.join("assets", filename)

                if os.path.isfile(path) and filename.lower().endswith(".png"):
                    image = pygame.image.load(path).convert_alpha()
                    self.assets[filename] = image

        # Load screen-specific assets (override global if same name)
        if os.path.isdir(screen_folder):
            for filename in os.listdir(screen_folder):
                path = os.path.join(screen_folder, filename)

                if os.path.isfile(path) and filename.lower().endswith(".png"):
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
