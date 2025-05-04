import pygame
import sys
import math
from grid import SCREEN_WIDTH, SCREEN_HEIGHT, draw_grid, get_grid_coors
from jeeproute import JeepRoute
from passenger import Passenger, TravelGraph
from areas import AreaManager, draw_waiting_pin

pygame.init()

# Constants
FPS = 120
MAX_PASSENGERS = 10000
BASE_SPAWN_RATE = 200
SPEED_MULTIPLIERS = [0, 0.05, 1.0, 5.0, 25.0, 50.0, 100.0]
PIN_TEXT_COLOR = (255, 255, 255)  # White text for pin numbers
COLORS = {
    'ROYAL_BLUE': (110, 115, 209),
    'RED': (252, 35, 20),
    'GREEN': (31, 149, 61),
    'PINK': (248, 167, 200),
    'YELLOW': (248, 193, 38),
    'GRAY': (163, 163, 163)
}

# Initialize core objects
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Jeepney Simulation")

# Fonts
futuralt = pygame.font.Font('FUTURALT.TTF', 24)
small_font = pygame.font.Font('FUTURALT.TTF', 18)

# Simulation state
sim_state = {
    'speed_index': 2,
    'active_passengers': [],
    'waiting_passengers': {},  # Will now store {position: {jeep_id: count}}
    'grid_cache': {},
    'metrics': {
        'total_commute': 0.0,
        'total_wait': 0.0,
        'total_fitness': 0.0,
        'completed': 0
    }
}

# Initialize routes and travel graph
routes = [JeepRoute(color=color) for color in COLORS.values()]
travel_graph = TravelGraph()
for i, route in enumerate(routes):
    travel_graph.addJeep(route, jeep_id=i)
travel_graph.add_transfer_connections()

# Initialize areas
area_manager = AreaManager(grid_size=17)
residential = [(2, 2), (3, 5), (4, 3), (5, 7), (6, 4),
               (0, 0), (0, 16), (16, 0), (16, 16), (0, 8), (8, 0)]
non_residential = [(10, 10), (12, 8), (13, 14), (15, 11), (11, 13),
                   (16, 8), (8, 16), (0, 12), (12, 0), (16, 4), (4, 16)]

area_manager.define_areas(residential, non_residential)

def format_time(seconds):
    return f"{int(seconds/60)}m {int(seconds%60)}s"

def handle_speed_change(key):
    if key == pygame.K_RIGHT:
        sim_state['speed_index'] = min(len(SPEED_MULTIPLIERS)-1,
                                       sim_state['speed_index']+1)
    elif key == pygame.K_LEFT:
        sim_state['speed_index'] = max(0, sim_state['speed_index']-1)

    sim_state['target_speed'] = SPEED_MULTIPLIERS[sim_state['speed_index']]

def spawn_passengers(dt):
    spawn_rate = BASE_SPAWN_RATE / 60 * dt
    spawn_count = int(spawn_rate + sim_state.get('spawn_remainder', 0))
    sim_state['spawn_remainder'] = spawn_rate + sim_state.get('spawn_remainder', 0) - spawn_count

    for _ in range(spawn_count):
        if len(sim_state['active_passengers']) >= MAX_PASSENGERS:
            break
        
        orig, dest = area_manager.get_random_origin_destination_pair()
        if not orig or not dest:
            continue
            
        p = Passenger()
        p.journey_time = 0.0  # Initialize journey_time to avoid AttributeError
        p.set_trip_between_areas(orig, dest)
        p.plan_route(travel_graph)
        
        if p.route:
            start = p.route[0]
            if start not in sim_state['grid_cache']:
                sim_state['grid_cache'][start] = get_grid_coors(*start)
            p.position = sim_state['grid_cache'][start]
            sim_state['active_passengers'].append(p)

def update_passengers(dt):
    # Reset the waiting data structure for this cycle
    waiting = {}
    completed = []
    
    for p in sim_state['active_passengers']:
        if p.state == "arrived":
            completed.append(p)
            sim_state['metrics']['total_commute'] += p.journey_time
            sim_state['metrics']['total_fitness'] += 100 * math.exp(-p.journey_time/60)
            continue
            
        p.update_position(travel_graph, dt, routes)
        p.journey_time += dt
        
        # Only count passengers who are actively waiting for a jeep
        if p.state == "waiting_jeep":
            # Get the current grid position
            current_node = p.route[p.current_step]
            grid_pos = current_node[0] if isinstance(current_node, tuple) and len(current_node) == 3 else current_node
            
            # Determine which jeep the passenger is waiting for
            jeep_id = -1  # Default value
            # If we're at a route node with destination info, extract the jeep_id
            current_node = p.route[p.current_step]
            if isinstance(current_node, tuple) and len(current_node) == 3:
                jeep_id = current_node[2]  # The jeep_id should be the third element in the tuple
            
            # Initialize the dict for this grid position if it doesn't exist
            if grid_pos not in waiting:
                waiting[grid_pos] = {}
            
            # Increment the count for this jeep at this position
            waiting[grid_pos][jeep_id] = waiting[grid_pos].get(jeep_id, 0) + 1

    # Clean up completed passengers
    sim_state['active_passengers'] = [p for p in sim_state['active_passengers'] if p not in completed]
    sim_state['metrics']['completed'] += len(completed)
    
    # Update waiting passengers
    sim_state['waiting_passengers'] = waiting
    
    # Update total wait time
    total_waiting = sum(sum(counts.values()) for counts in waiting.values())
    sim_state['metrics']['total_wait'] += total_waiting * dt

def draw_waiting_pins(screen, font):
    """Draw pins showing waiting passengers, colored by the jeep they're waiting for."""
    PIN_SPACING = 15  # Space between multiple pins at the same location
    
    for pos, jeep_counts in sim_state['waiting_passengers'].items():
        if pos not in sim_state['grid_cache']:
            sim_state['grid_cache'][pos] = get_grid_coors(*pos)
        
        screen_pos = sim_state['grid_cache'][pos]
        
        # Calculate total pins to place at this position
        total_pins = len(jeep_counts)
        if total_pins == 0:
            continue
            
        # Calculate the starting x-offset for multiple pins
        start_offset = -((total_pins - 1) * PIN_SPACING) / 2
        
        # Draw pins for each jeep type
        for i, (jeep_id, count) in enumerate(jeep_counts.items()):
            if count <= 0:
                continue
                
            # Calculate the x-offset for this pin
            offset_x = start_offset + (i * PIN_SPACING)
            
            # Get the pin color based on the jeep route
            pin_color = COLORS['GRAY']  # Default gray
            if jeep_id >= 0 and jeep_id < len(routes):
                pin_color = routes[jeep_id].color
            
            # Adjust position to account for multiple pins
            pin_pos = (screen_pos[0] + offset_x, screen_pos[1])
            
            # Draw the pin with the appropriate color
            draw_waiting_pin(screen, pin_pos, count, font, pin_color)

def draw_interface():
    # Stats
    stats = [
        f"Average Wait: {format_time(sim_state['metrics']['total_wait']/(sim_state['metrics']['completed'] or 1))}",
        f"Completed: {sim_state['metrics']['completed']}",
        f"Active: {len(sim_state['active_passengers'])}",
        f"Waiting: {sum(sum(counts.values()) for counts in sim_state['waiting_passengers'].values())}",
        f"Fitness: {sim_state['metrics']['total_fitness']/(sim_state['metrics']['completed'] or 1):.1f}"
    ]
    
    y = 20
    for text in stats:
        surf = futuralt.render(text, True, (0,0,0))
        screen.blit(surf, (20, y))
        y += 30
    
    # Speed display
    speed_text = f"{sim_state['current_speed']:.2f}× Speed"
    surf = small_font.render(speed_text, True, (0,0,0))
    screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, 20))
    
def main_loop():
    last_time = pygame.time.get_ticks()
    # Initialize current_speed and target_speed if not present
    if 'current_speed' not in sim_state:
        sim_state['current_speed'] = SPEED_MULTIPLIERS[sim_state['speed_index']]
    if 'target_speed' not in sim_state:
        sim_state['target_speed'] = SPEED_MULTIPLIERS[sim_state['speed_index']]

    while True:
        now = pygame.time.get_ticks()
        raw_dt = (now - last_time) / 1000.0
        last_time = now

        # Lerp current_speed toward target_speed over ~0.1s
        alpha = min(1.0, raw_dt / 0.1)
        cs = sim_state['current_speed']
        ts = sim_state['target_speed']
        sim_state['current_speed'] = cs + (ts - cs) * alpha

        # For Smoothing
        dt = raw_dt * sim_state['current_speed']

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                handle_speed_change(event.key)

        # Update
        spawn_passengers(dt)
        update_passengers(dt)

        # Draw
        draw_grid(screen)
        area_manager.draw(screen)

        # Draw all routes
        for r in routes:
            r.drawRoute(screen)

        # Draw all passengers
        for p in sim_state['active_passengers']:
            p.draw(screen)

        # Draw all jeeps
        for r in routes:
            r.update(dt)
            r.drawJeep(screen)

        # Draw all waiting pins
        draw_waiting_pins(screen, area_manager.font)

        draw_interface()
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main_loop()