import pygame
import grid
import sys
from jeeproute import JeepRoute

# INITIALIZATIONS ===================================
pygame.init()

# CONSTANTS =========================================
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 60  # Increased FPS for smoother animation

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
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # When mouse is clicked, capture position and set it as start point
            if event.button == 1:  # Left click for start point
                # Convert screen position to grid position
                grid_width = grid.GRID_COLS * grid.CELL_SIZE
                grid_height = grid.GRID_ROWS * grid.CELL_SIZE
                grid_x = (grid.SCREEN_WIDTH - grid_width) // 2
                grid_y = (grid.SCREEN_HEIGHT - grid_height) // 2 - 25
                
                x = (event.pos[0] - grid_x) // grid.CELL_SIZE
                y = (event.pos[1] - grid_y) // grid.CELL_SIZE
                
                # Ensure coordinates are within grid bounds
                x = max(0, min(x, grid.GRID_COLS))
                y = max(0, min(y, grid.GRID_ROWS))
              
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