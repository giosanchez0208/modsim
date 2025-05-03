import pygame
import grid
import sys
from jeeproute import JeepRoute

# INITIALIZATIONS ===================================
pygame.init()

# CONSTANTS =========================================
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60

# COLORS (from the screenshot) ======================
ROYAL_BLUE = (110, 115, 209)  
RED = (252, 35, 20)           
GREEN = (31, 149, 61)         
PINK = (248, 167, 200)       
YELLOW = (248, 193, 38)       
GRAY = (163, 163, 163)

# CREATE SCREEN =====================================
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jeepney Simulation")
clock = pygame.time.Clock() 

# Generate jeep routes w different colors
routes = [
    JeepRoute(color=ROYAL_BLUE),
    JeepRoute(color=RED),
    JeepRoute(color=GREEN),
    JeepRoute(color=PINK),
    JeepRoute(color=YELLOW),
    JeepRoute(color=GRAY),
]

# Main loop
running = True
last_time = pygame.time.get_ticks()

while running:
    # Calculate delta time (time elapsed since last frame) in seconds
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0 
    last_time = current_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
              
    # Draw the grid
    grid.draw_grid(screen)
    
    # Update all jeeps with delta time
    for route in routes:
        route.update(dt)

    # Draw all jeep routes
    for route in routes:
        route.drawRoute(screen)

    # Draw all jeeps
    for route in routes:
        route.drawJeep(screen)
    
    # Update the display
    pygame.display.flip()
    
    # Control the frame rate
    clock.tick(FPS)

# Quit pygame
pygame.quit()
sys.exit()