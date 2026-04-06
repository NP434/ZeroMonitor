import pygame

pygame.font.init()

# Colors - Primary Palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (25, 25, 25)
GRAY = (60, 60, 60)
LIGHT_GRAY = (120, 120, 120)
LIGHTER_GRAY = (140, 140, 140)

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

# Fonts - Improved typography hierarchy
DEFAULT_FONT = pygame.font.SysFont("Arial", 16)
FONT_SMALL = pygame.font.SysFont("Arial", 14)
FONT_MEDIUM = pygame.font.SysFont("Arial", 18, bold=False)
FONT_LARGE = pygame.font.SysFont("Arial", 24, bold=True)
FONT_XLARGE = pygame.font.SysFont("Arial", 32, bold=True)
FONT_TITLE = pygame.font.SysFont("Arial", 40, bold=True)

# Spacing constants
PADDING_SMALL = 8
PADDING_MEDIUM = 12
PADDING_LARGE = 16
PADDING_XLARGE = 24

MARGIN_SMALL = 8
MARGIN_MEDIUM = 12
MARGIN_LARGE = 16
MARGIN_XLARGE = 24

GAP_SMALL = 8
GAP_MEDIUM = 12
GAP_LARGE = 16

# Component sizes
CORNER_RADIUS = 12
BORDER_WIDTH_THIN = 1
BORDER_WIDTH_MEDIUM = 2
BORDER_WIDTH_THICK = 3

# Button styling
BUTTON_BG = BLUE
BUTTON_TEXT = WHITE
BUTTON_RADIUS = 10
BUTTON_PADDING = 12
BUTTON_MIN_HEIGHT = 44

# Card styling
CARD_BG = (30, 30, 30)
CARD_BORDER_WIDTH = 2
CARD_CORNER_RADIUS = 12
CARD_PADDING = 16

# Top bar
TOPBAR_HEIGHT = 90
TOPBAR_BG = DARK_GRAY
TOPBAR_BORDER_WIDTH = 2
TOPBAR_BORDER_COLOR = BLUE

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