import pygame
import sys

# initialize pygame
pygame.init()
running = True

# set screen size to match LCD resolution
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simulated 1024x600 LCD Screen")

# Colors (though there are defaults provided)
BLACK = (0,0,0)
WHITE = (255, 255, 255)
GRAY = (60, 60, 60)
BLUE = (0, 120, 255)

# Font
font = pygame.font.SysFont("Arial", 32)

# Button dimensions
button_width = 160
button_height = 60
button_x = SCREEN_WIDTH - button_width - 20
button_y = 20

settings_button = pygame.Rect(button_x, button_y, button_width, button_height)

# Main loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if settings_button.collidepoint(event.pos):
                print("Settings button pressed!")

    # Fill screen       
    screen.fill(BLACK)

    # Draw settings button
    pygame.draw.rect(screen, BLUE, settings_button, border_radius=10)

    # Draw button text
    text_surface = font.render("Settings", True, WHITE)
    text_rect = text_surface.get_rect(center=settings_button.center)
    screen.blit(text_surface, text_rect)

    # Draw rectangle
    pygame.draw.rect(screen, GRAY, (50, 300, 924, 120))

    # draw text
    text_surface = font.render("Zero Monitor 1024x600 LCD Simulation!", True, WHITE)
    screen.blit(text_surface, (60, 350))



    # Update display
    pygame.display.flip()