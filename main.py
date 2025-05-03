# Pre-calculate grid coordinates for performance
grid_coordinates_cache = {}

from passenger import Passenger, TravelGraph
import pygame
import grid
import sys
import random
from jeeproute import JeepRoute

# INITIALIZATIONS ===================================
pygame.init()

# CONSTANTS =========================================
# For the simulation
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
FPS = 120

# For passenger generation
MAX_PASSENGERS = 10000
BASE_SPAWN_RATE = 300  # Passengers per simulation minute at 1x speed
time_since_last_spawn = 0
active_passengers = []

# COLORS (from the screenshot) ======================
ROYAL_BLUE = (110, 115, 209)  
RED = (252, 35, 20)           
GREEN = (31, 149, 61)         
PINK = (248, 167, 200)       
YELLOW = (248, 193, 38)       
GRAY = (163, 163, 163)

# FONTS
futuralt_font = pygame.font.Font('FUTURALT.TTF', 24)

# Speed settings
SPEED_MULTIPLIERS = [1.0, 25.0, 50.0]
current_speed_index = 0
speed_multiplier = SPEED_MULTIPLIERS[current_speed_index]
font = pygame.font.SysFont('Arial', 24)

# Commute time tracking
total_commute_time = 0
completed_journeys = 0
# Performance optimization: removed arrived_this_frame list

# Initialize last_stats_values to an empty dictionary
last_stats_values = {}

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

# Generate Travel Graph
travel_graph = TravelGraph()
for i, route in enumerate(routes):
    travel_graph.addJeep(route, jeep_id=i)
travel_graph.add_transfer_connections()

# Helper function to format time
def format_time(seconds):
    minutes = int(seconds / 60)
    seconds = int(seconds % 60)
    return f"{minutes}m {seconds}s"

# Pre-calculate grid coordinates for performance
grid_coordinates_cache = {}

# Main loop
running = True
last_time = pygame.time.get_ticks()
spawn_counter = 0.0  # Track fractional spawns

while running:
    current_time = pygame.time.get_ticks()
    dt = (current_time - last_time) / 1000.0 * speed_multiplier
    raw_dt = (current_time - last_time) / 1000.0
    last_time = current_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                current_speed_index = 0
                speed_multiplier = SPEED_MULTIPLIERS[current_speed_index]
            elif event.key == pygame.K_2:
                current_speed_index = 1
                speed_multiplier = SPEED_MULTIPLIERS[current_speed_index]
            elif event.key == pygame.K_3:
                current_speed_index = 2
                speed_multiplier = SPEED_MULTIPLIERS[current_speed_index]

    # Passenger spawning based on dt and speed
    # Calculate expected number of spawns this frame
    spawn_rate_per_second = BASE_SPAWN_RATE / 60.0  # Convert from per minute to per second
    expected_spawns = spawn_rate_per_second * dt  # Scale by dt which already includes speed multiplier
    
    # Add to counter
    spawn_counter += expected_spawns
    
    # Spawn whole passengers
    while spawn_counter >= 1.0 and len(active_passengers) < MAX_PASSENGERS:
        spawn_counter -= 1.0
        if random.random() < 0.7:  # 70% chance to spawn
            new_passenger = Passenger()
            new_passenger.set_random_trip()
            new_passenger.plan_route(travel_graph)
            if new_passenger.route:
                new_passenger.state = "walking"
                # Use cached grid coordinates if available
                start_point = new_passenger.route[0]
                if start_point in grid_coordinates_cache:
                    new_passenger.position = grid_coordinates_cache[start_point]
                else:
                    new_passenger.position = grid.get_grid_coors(*start_point)
                    grid_coordinates_cache[start_point] = new_passenger.position
                new_passenger.journey_time = 0
                active_passengers.append(new_passenger)

    # Draw the grid
    grid.draw_grid(screen)

    # Update all jeeps
    for route in routes:
        route.update(dt)
        route.drawRoute(screen)
    for route in routes:
        route.update(dt)
        route.drawJeep(screen)
    # Update and draw passengers - removing passengers that arrive
    for i in range(len(active_passengers)-1, -1, -1):  # Iterate backwards for safe removal
        p = active_passengers[i]
        if p.state == "arrived":
            # Update statistics for arrived passengers immediately
            total_commute_time += p.journey_time
            completed_journeys += 1
            # Remove from list
            active_passengers.pop(i)
        else:
            # Only update and draw passengers still in transit
            p.update_position(travel_graph, dt, routes)
            p.draw(screen)
            p.journey_time += dt

    # Update statistics display - render only when changed to avoid flashing
    avg_time = (total_commute_time / completed_journeys) if completed_journeys > 0 else 0
    current_spawn_rate = BASE_SPAWN_RATE * speed_multiplier / 60
    
    # Check if any values have changed
    current_stats = {
        "avg_time": int(avg_time),  # Only update when seconds change
        "completed": completed_journeys,
        "active": len(active_passengers),
        "spawn_rate": round(current_spawn_rate, 1)
    }
    
    # If values changed or first frame, regenerate text surfaces
    if current_stats != last_stats_values or not stats_surfaces:
        last_stats_values = current_stats.copy()
        stats_surfaces = []
        
        stats_text = [
            f"Average Commute Time: {format_time(avg_time)}",
            f"Completed Journeys: {completed_journeys}",
            f"Active Passengers: {len(active_passengers)}",
            f"Spawn Rate: {current_spawn_rate:.1f} per second"
        ]
        
        for text in stats_text:
            stats_surfaces.append(futuralt_font.render(text, True, (0, 0, 0)))
    
    # Always display the pre-rendered surfaces
    y_offset = 20
    for surface in stats_surfaces:
        screen.blit(surface, (20, y_offset))
        y_offset += 30

    # Speed indicator - only re-render when speed changes
    if not hasattr(pygame, 'speed_text_surface') or speed_multiplier != getattr(pygame, 'last_speed_multiplier', None):
        pygame.speed_text_surface = futuralt_font.render(f'{int(speed_multiplier)}x Speed', True, (0, 0, 0))
        pygame.last_speed_multiplier = speed_multiplier
    
    text_rect = pygame.speed_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
    screen.blit(pygame.speed_text_surface, text_rect.topleft)

    # Update the display
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()