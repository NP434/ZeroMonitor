import pygame

pygame.font.init()

# Colors
WHITE = (255,255,255)
BLACK = (0, 0, 0)
GRAY = (60, 60, 60)
BLUE = (0, 120, 255)
GREEN = (46, 204, 113)
YELLOW = (241, 196, 15)
RED = (231, 76, 60)

# Default Font
DEFAULT_FONT = pygame.font.SysFont("Arial", 32)

# Default button styling
BUTTON_BG = BLUE
BUTTON_TEXT = WHITE
BUTTON_RADIUS = 10

# Status Colors
STATUS_COLORS = {
    "Available": GREEN,
    "Degraded": YELLOW,
    "Offline": RED
}