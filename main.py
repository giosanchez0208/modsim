import pygame
import sys
import random
import grid
from passenger import Passenger, TravelGraph
from jeeproute import JeepRoute
from areas import AreaManager

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

# Commute time tracking
total_commute_time = 0
completed_journeys = 0

# Initialize last_stats_values to an empty dictionary
last_stats_values = {}
stats_surfaces = []

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

# Initialize the Area Manager
area_manager = AreaManager(grid_size=17)

# Define residential and non-residential areas
# Residential areas - could be customized or randomized
residential_positions = [
    (2, 3), (5, 8), (8, 2), (12, 6), (15, 14)
]

# Non-residential areas - could be customized or randomized
non_residential_positions = [
    (4, 15), (7, 10), (9, 6), (11, 13), (14, 4)
]

# Set up the areas
area_manager.define_areas(residential_positions, non_residential_positions)

# Dictionary to track waiting passengers at each node (grid coordinates)
waiting_passengers = {}

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
            elif event.key == pygame.K_r:
                # Randomize areas when R is pressed
                area_manager.generate_random_areas(num_residential=5, num_non_residential=5)
                # Reset waiting passengers dictionary
                waiting_passengers = {}
                for area in area_manager.all_areas:
                    waiting_passengers[area] = 0

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
            # Get random origin and destination from areas
            origin, destination = area_manager.get_random_origin_destination_pair()
            
            if origin and destination:
                new_passenger = Passenger()
                new_passenger.set_trip_between_areas(origin, destination)
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
    
    # Draw the areas
    area_manager.draw(screen)

    # Update all jeeps
    for route in routes:
        route.update(dt)
        route.drawRoute(screen)
    for route in routes:
        route.update(dt)
        route.drawJeep(screen)
        
    # Reset waiting passenger counts each frame
    waiting_passengers = {}
    
    # Update and draw passengers - removing passengers that arrive
    for i in range(len(active_passengers)-1, -1, -1):  # Iterate backwards for safe removal
        p = active_passengers[i]
        
        # Track waiting passengers at transition nodes
        if p.state == "waiting_jeep" and p.current_step < len(p.route):
            # Get the current transition node where passenger is waiting
            current_node = p.route[p.current_step]
            
            # For transition nodes, we need the base grid coordinates
            if isinstance(current_node, tuple) and len(current_node) == 3 and current_node[1] == 'transition':
                node_pos = current_node[0]  # Extract the grid coordinates
                
                # Increment the count for this location
                if node_pos in waiting_passengers:
                    waiting_passengers[node_pos] += 1
                else:
                    waiting_passengers[node_pos] = 1
        
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
    
    # Update the area manager with current waiting counts
    for pos, count in waiting_passengers.items():
        area_manager.update_waiting_count(pos, count)

    # Update statistics display - render only when changed to avoid flashing
    avg_time = (total_commute_time / completed_journeys) if completed_journeys > 0 else 0
    current_spawn_rate = BASE_SPAWN_RATE * speed_multiplier / 60
    
    # Check if any values have changed
    current_stats = {
        "avg_time": int(avg_time),  # Only update when seconds change
        "completed": completed_journeys,
        "active": len(active_passengers),
        "spawn_rate": round(current_spawn_rate, 1),
        "waiting_total": sum(waiting_passengers.values())
    }
    
    # If values changed or first frame, regenerate text surfaces
    if current_stats != last_stats_values:
        last_stats_values = current_stats.copy()
        stats_surfaces = []
        
        stats_text = [
            f"Average Commute Time: {format_time(avg_time)}",
            f"Completed Journeys: {completed_journeys}",
            f"Active Passengers: {len(active_passengers)}",
            f"Waiting Passengers: {sum(waiting_passengers.values())}",
            f"Spawn Rate: {current_spawn_rate:.1f} per second",
            f"Press R to randomize areas"
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