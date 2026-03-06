import pygame

pygame.font.init()

# Colors - Primary Palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
GRAY = (60, 60, 60)
LIGHT_GRAY = (100, 100, 100)

# Colors - Status & Severity
BLUE = (0, 120, 255)
BRIGHT_BLUE = (100, 180, 255)
GREEN = (46, 204, 113)
BRIGHT_GREEN = (76, 255, 143)
YELLOW = (241, 196, 15)
BRIGHT_YELLOW = (255, 223, 0)
RED = (231, 76, 60)
BRIGHT_RED = (255, 100, 100)
POWER_RED = (200, 50, 50)
DARK_RED = (139, 0, 0)
ORANGE = (230, 126, 34)
PURPLE = (106, 13, 103)

# Fonts
DEFAULT_FONT = pygame.font.SysFont("Arial", 32)
FONT_SMALL = pygame.font.SysFont("Arial", 20)
FONT_MEDIUM = pygame.font.SysFont("Arial", 26)
FONT_LARGE = pygame.font.SysFont("Arial", 32, bold=True)
FONT_XLARGE = pygame.font.SysFont("Arial", 48, bold=True)

# Default button styling
BUTTON_BG = BLUE
BUTTON_TEXT = WHITE
BUTTON_RADIUS = 10

# Status Colors
STATUS_COLORS = {
    "Available": GREEN,
    "Degraded": YELLOW,
    "Offline": RED,
    "normal": GREEN,
    "warning": YELLOW,
    "critical": ORANGE,
    "severe": RED
}