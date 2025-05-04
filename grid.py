import pygame

# CONSTANTS =========================================
# Screen
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
# Colors
BACKGROUND_COLOR = (240, 235, 231)
GRID_COLOR = (206, 195, 188)
# Variables
CELL_SIZE = 50
GRID_ROWS = 16
GRID_COLS = 16
GRID_LINE_WIDTH = 1

# Function to draw the grid =========================
def draw_grid(screen):
    # Calculate grid position
    grid_width = GRID_COLS * CELL_SIZE
    grid_height = GRID_ROWS * CELL_SIZE
    grid_x = (SCREEN_WIDTH - grid_width) // 2 
    grid_y = (SCREEN_HEIGHT - grid_height) // 2 + 20

    # Fill the background
    screen.fill(BACKGROUND_COLOR)

    # Draw the grid
    for row in range(GRID_ROWS + 1):
        pygame.draw.line(screen, GRID_COLOR, 
                         (grid_x, grid_y + row * CELL_SIZE), 
                         (grid_x + grid_width, grid_y + row * CELL_SIZE), 
                         GRID_LINE_WIDTH)
    for col in range(GRID_COLS + 1):
        pygame.draw.line(screen, GRID_COLOR, 
                         (grid_x + col * CELL_SIZE, grid_y), 
                         (grid_x + col * CELL_SIZE, grid_y + grid_height), 
                         GRID_LINE_WIDTH)

def get_grid_coors(x, y):
    # top left corner is (0,0),
    # bottom right corner is (16,16)
    grid_width = GRID_COLS * CELL_SIZE
    grid_height = GRID_ROWS * CELL_SIZE
    grid_x = (SCREEN_WIDTH - grid_width) // 2
    grid_y = (SCREEN_HEIGHT - grid_height) // 2 + 20

    return (
        grid_x + x * CELL_SIZE,
        grid_y + y * CELL_SIZE
    )