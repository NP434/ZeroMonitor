# Abstract base class for screens
class BaseScreen:
    """
    Abstract Base Class with methods that will be used in all screens
    """
    def __init__(self, app):
        self.app = app

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
