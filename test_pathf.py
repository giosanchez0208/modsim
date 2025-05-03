import pygame
import sys
import random
import math
from jeeproute import JeepRoute
from passenger import TravelGraph, Passenger
import grid

pygame.init()

screen = pygame.display.set_mode((grid.SCREEN_WIDTH, grid.SCREEN_HEIGHT))
pygame.display.set_caption("Pathfinding Test - Passenger Journey")
clock = pygame.time.Clock()

JEEP_COLORS = [
    (255, 0, 0),     # Red
    (0, 0, 255),     # Blue
    (0, 128, 0),     # Green
    (255, 165, 0),   # Orange
    (128, 0, 128),   # Purple
    (0, 128, 128),   # Teal
    (128, 128, 0),   # Olive
    (255, 20, 147)   # Pink
]

WALKING_COLOR = (100, 100, 100)      # Gray for walking
BOARDING_COLOR = (50, 205, 50)       # Lime Green for boarding
ALIGHTING_COLOR = (255, 69, 0)       # OrangeRed for alighting
TRANSFER_COLOR = (255, 215, 0)       # Gold for transfers

# Define action types for better path analysis
ACTION_WALK = "walk"
ACTION_BOARD = "board"
ACTION_RIDE = "ride"
ACTION_ALIGHT = "alight"
ACTION_TRANSFER = "transfer"

def generate_test_case():
    num_jeeps = random.randint(2, 5)
    
    jeeps = []
    for i in range(num_jeeps):
        color = JEEP_COLORS[i % len(JEEP_COLORS)]
        jeep = JeepRoute(color=color)
        jeeps.append(jeep)
    
    # Set up the travel graph
    travel_graph = TravelGraph()
    
    # Add jeeps to travel graph
    all_route_points = {}
    for i, jeep in enumerate(jeeps):
        # Use the index as a unique jeep_id
        travel_graph.addJeep(jeep, jeep_id=i)
        # Save route points with their jeep index for coloring the path later
        for point in jeep.route_points:
            if point in all_route_points:
                all_route_points[point].append(i)
            else:
                all_route_points[point] = [i]
    
    # Add connections for transfers between jeep routes
    travel_graph.add_transfer_connections()
    
    # Generate random start and end points
    # Make sure they're not on the same spot
    while True:
        start_x, start_y = random.randint(0, 16), random.randint(0, 16)
        end_x, end_y = random.randint(0, 16), random.randint(0, 16)
        if (start_x, start_y) != (end_x, end_y):
            break
    
    start_point = (start_x, start_y)
    end_point = (end_x, end_y)
    
    # Create passenger and plan route
    passenger = Passenger(origin=start_point, destination=end_point)
    passenger.plan_route(travel_graph)
    
    path = passenger.route
    cost = passenger.cost
    
    # Analyze the path to understand journey segments
    journey_segments = analyze_journey(path, travel_graph)
    
    print(f"Generated {num_jeeps} jeep routes")
    print(f"Path found from {start_point} to {end_point}")
    print(f"Total cost: {cost}")
    print(f"Path length: {len(path)} points")
    
    # Print journey analysis
    print("\nJourney Analysis:")
    print_journey_analysis(journey_segments)
    
    return jeeps, path, start_point, end_point, all_route_points, journey_segments, travel_graph

def analyze_journey(path, travel_graph):
    """Analyze the journey to identify segments of walking, riding, boarding, etc."""
    if not path or len(path) < 2:
        return []
    
    segments = []
    current_segment = None
    
    for i in range(len(path) - 1):
        curr = path[i]
        next_node = path[i + 1]
        
        # Find the edge between these nodes
        edge_cost = None
        edge_type = None
        
        for neighbor, cost, edge in travel_graph.graph.get(curr, []):
            if neighbor == next_node:
                edge_cost = cost
                edge_type = edge
                break
        
        if edge_type == "walk":
            action_type = ACTION_WALK
        elif edge_type == "transition":
            action_type = ACTION_BOARD
            # Extract jeep_id from next node which should be a transition node
            jeep_id = next_node[2] if len(next_node) == 3 else None
        elif edge_type == "jeep":
            action_type = ACTION_RIDE
            # Extract jeep_id from current node which should be a transition node
            jeep_id = curr[2] if len(curr) == 3 else None
        elif edge_type == "alight":
            action_type = ACTION_ALIGHT
        elif edge_type == "transfer" or edge_type == "complete_transfer":
            action_type = ACTION_TRANSFER
            if edge_type == "transfer" and len(next_node) == 3 and next_node[1] == 'transfer':
                # Extract transfer info (from_jeep, to_jeep)
                transfer_info = next_node[2]
            else:
                transfer_info = None
        else:
            action_type = edge_type  # Default to edge type if not specifically handled
        
        # Create segment info
        segment = {
            "from_node": curr,
            "to_node": next_node,
            "action": action_type,
            "cost": edge_cost
        }
        
        # Add jeep info if applicable
        if action_type in [ACTION_BOARD, ACTION_RIDE] and 'jeep_id' in locals():
            segment["jeep_id"] = jeep_id
        
        # Add transfer info if applicable
        if action_type == ACTION_TRANSFER and 'transfer_info' in locals() and transfer_info:
            segment["from_jeep"] = transfer_info[0]
            segment["to_jeep"] = transfer_info[1]
        
        segments.append(segment)
    
    return segments

def print_journey_analysis(journey_segments):
    """Print a human-readable analysis of the journey"""
    if not journey_segments:
        print("No journey to analyze")
        return
    
    total_cost = sum(segment["cost"] for segment in journey_segments)
    
    # Count different actions
    walk_segments = sum(1 for segment in journey_segments if segment["action"] == ACTION_WALK)
    boardings = sum(1 for segment in journey_segments if segment["action"] == ACTION_BOARD)
    rides = sum(1 for segment in journey_segments if segment["action"] == ACTION_RIDE)
    alightings = sum(1 for segment in journey_segments if segment["action"] == ACTION_ALIGHT)
    transfers = sum(1 for segment in journey_segments if segment["action"] == ACTION_TRANSFER)
    
    print(f"Total journey cost: {total_cost}")
    print(f"Walking segments: {walk_segments}")
    print(f"Jeepney boardings: {boardings}")
    print(f"Jeepney rides: {rides}")
    print(f"Alightings: {alightings}")
    print(f"Transfers between jeepneys: {transfers}")
    
    # Detailed journey steps
    print("\nDetailed Journey Steps:")
    current_mode = None
    current_jeep = None
    step_num = 1
    
    for i, segment in enumerate(journey_segments):
        action = segment["action"]
        
        if action == ACTION_WALK:
            if current_mode != ACTION_WALK:
                print(f"{step_num}. Started walking from {segment['from_node']}")
                step_num += 1
                current_mode = ACTION_WALK
        
        elif action == ACTION_BOARD:
            jeep_id = segment.get("jeep_id", "unknown")
            print(f"{step_num}. Boarded jeepney {jeep_id} at {segment['from_node']}")
            step_num += 1
            current_mode = ACTION_RIDE
            current_jeep = jeep_id
        
        elif action == ACTION_RIDE:
            # We don't need to print every ride segment, just the first one after boarding
            pass
        
        elif action == ACTION_ALIGHT:
            print(f"{step_num}. Alighted from jeepney {current_jeep} at {segment['to_node']}")
            step_num += 1
            current_mode = None
            current_jeep = None
        
        elif action == ACTION_TRANSFER:
            if "from_jeep" in segment and "to_jeep" in segment:
                print(f"{step_num}. Transferred from jeepney {segment['from_jeep']} to jeepney {segment['to_jeep']} at {segment['from_node'][0]}")
            else:
                print(f"{step_num}. Made a transfer at {segment['from_node']}")
            step_num += 1
    
    # Print final arrival
    if journey_segments:
        final_destination = journey_segments[-1]["to_node"]
        if isinstance(final_destination, tuple) and len(final_destination) == 2:
            print(f"{step_num}. Arrived at destination {final_destination}")

def main():
    # Generate initial test case
    jeeps, path, start_point, end_point, all_route_points, journey_segments, travel_graph = generate_test_case()
    
    # Instructions text
    font = pygame.font.SysFont('Arial', 24)
    instructions = font.render('SPACE to generate new test case', True, (0, 0, 0))
    
    show_info = False
    info_panel = None
    
    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:  # Press SPACE to regenerate
                    jeeps, path, start_point, end_point, all_route_points, journey_segments, travel_graph = generate_test_case()
                    show_info = False
                elif event.key == pygame.K_i:  # Press I to toggle journey info
                    show_info = not show_info
        
        # Draw everything
        screen.fill((255, 255, 255))  # Clear with white background
        grid.draw_grid(screen)
        
        # Draw instructions
        screen.blit(instructions, (50, 20))
        
        # Draw jeep routes first (background)
        for jeep in jeeps:
            jeep.drawRoute(screen)
        
        # Draw direction arrows next
        for jeep in jeeps:
            draw_route_arrows(screen, jeep)
        
        # Draw path with different colors for walking, boarding, riding, alighting
        draw_enhanced_path(screen, path, all_route_points, jeeps, journey_segments)
        
        # Draw start and end points (always on top)
        draw_point(screen, start_point, (0, 255, 0), 10)  # Green for start
        draw_point(screen, end_point, (255, 0, 255), 10)  # Magenta for end
        
        # Draw journey info panel if toggled on
        if show_info:
            draw_journey_info(screen, journey_segments, jeeps)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

def draw_route_arrows(screen, jeep):
    # Draw direction arrows along the jeep route
    route_points = jeep.route_points
    if len(route_points) < 2:
        return
        
    for i in range(len(route_points)):
        current = route_points[i]
        next_point = route_points[(i + 1) % len(route_points)]
        
        # Get screen coordinates
        sx, sy = grid.get_grid_coors(*current)
        ex, ey = grid.get_grid_coors(*next_point)
        
        # Only draw arrows for horizontal and vertical segments
        # Skip diagonal segments if any
        if current[0] != next_point[0] and current[1] != next_point[1]:
            continue
            
        # Calculate midpoint for arrow placement
        mx, my = (sx + ex) // 2, (sy + ey) // 2
        
        # Calculate arrow direction and draw
        dx, dy = ex - sx, ey - sy
        if dx == 0 and dy == 0:
            continue  # Skip if points are the same
            
        # Normalize and scale for arrow size
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx, dy = dx / length * 15, dy / length * 15
            
        # Draw arrow at midpoint
        pygame.draw.polygon(screen, jeep.color, [
            (mx, my),
            (mx - dy/2 - dx/2, my + dx/2 - dy/2),
            (mx + dy/2 - dx/2, my - dx/2 - dy/2)
        ])

def draw_enhanced_path(screen, path, all_route_points, jeeps, journey_segments):
    if not path or len(path) < 2 or not journey_segments:
        return
    
    # Draw segments of the path with different colors based on action type
    for i, segment in enumerate(journey_segments):
        from_node = segment["from_node"]
        to_node = segment["to_node"]
        action = segment["action"]
        
        # Skip nodes that aren't grid coordinates
        if not isinstance(from_node, tuple) or not isinstance(to_node, tuple):
            continue
        
        # Skip transition and transfer nodes for visualization purposes
        if isinstance(from_node, tuple) and len(from_node) > 2:
            from_node = from_node[0]  # Get the grid coordinate
        if isinstance(to_node, tuple) and len(to_node) > 2:
            to_node = to_node[0]  # Get the grid coordinate
            
        # Get screen coordinates
        from_screen = grid.get_grid_coors(*from_node) if isinstance(from_node, tuple) and len(from_node) == 2 else None
        to_screen = grid.get_grid_coors(*to_node) if isinstance(to_node, tuple) and len(to_node) == 2 else None
        
        if not from_screen or not to_screen:
            continue
            
        # Set color and line style based on action type
        if action == ACTION_WALK:
            color = WALKING_COLOR
            line_width = 3
            # Draw dashed line for walking
            draw_dashed_line(screen, (255, 255, 255), from_screen, to_screen, line_width + 2)
            draw_dashed_line(screen, color, from_screen, to_screen, line_width)
        
        elif action == ACTION_RIDE and "jeep_id" in segment:
            jeep_id = segment["jeep_id"]
            color = jeeps[jeep_id].color if jeep_id < len(jeeps) else (0, 0, 0)
            line_width = 8
            # Draw a thick line for riding
            pygame.draw.line(screen, (255, 255, 255), from_screen, to_screen, line_width + 4)
            pygame.draw.line(screen, color, from_screen, to_screen, line_width)
        
        elif action == ACTION_BOARD:
            # Draw boarding indicator
            pygame.draw.circle(screen, BOARDING_COLOR, from_screen, 12)
            pygame.draw.circle(screen, (255, 255, 255), from_screen, 10)
            pygame.draw.circle(screen, BOARDING_COLOR, from_screen, 8)
            
            # Draw small text indicating "BOARD"
            font = pygame.font.SysFont('Arial', 12)
            text = font.render('B', True, (0, 0, 0))
            text_rect = text.get_rect(center=from_screen)
            screen.blit(text, text_rect)
        
        elif action == ACTION_ALIGHT:
            # Draw alighting indicator
            pygame.draw.circle(screen, ALIGHTING_COLOR, to_screen, 12)
            pygame.draw.circle(screen, (255, 255, 255), to_screen, 10)
            pygame.draw.circle(screen, ALIGHTING_COLOR, to_screen, 8)
            
            # Draw small text indicating "ALIGHT"
            font = pygame.font.SysFont('Arial', 12)
            text = font.render('A', True, (0, 0, 0))
            text_rect = text.get_rect(center=to_screen)
            screen.blit(text, text_rect)
        
        elif action == ACTION_TRANSFER:
            # Get the actual grid point for the transfer
            if isinstance(from_node, tuple) and len(from_node) > 2:
                transfer_point = from_node[0]
            else:
                transfer_point = from_node
                
            transfer_screen = grid.get_grid_coors(*transfer_point) if isinstance(transfer_point, tuple) and len(transfer_point) == 2 else None
            
            if transfer_screen:
                # Draw transfer indicator
                pygame.draw.circle(screen, TRANSFER_COLOR, transfer_screen, 14)
                pygame.draw.circle(screen, (255, 255, 255), transfer_screen, 12)
                pygame.draw.circle(screen, TRANSFER_COLOR, transfer_screen, 10)
                
                # Draw small text indicating "TRANSFER"
                font = pygame.font.SysFont('Arial', 12)
                text = font.render('T', True, (0, 0, 0))
                text_rect = text.get_rect(center=transfer_screen)
                screen.blit(text, text_rect)

def draw_journey_info(screen, journey_segments, jeeps):
    """Draw an information panel showing journey details"""
    if not journey_segments:
        return
    
    # Panel size and position
    panel_width = 300
    panel_height = 400
    panel_x = grid.SCREEN_WIDTH - panel_width - 20
    panel_y = 70
    
    # Draw panel background
    pygame.draw.rect(screen, (240, 240, 240), (panel_x, panel_y, panel_width, panel_height))
    pygame.draw.rect(screen, (0, 0, 0), (panel_x, panel_y, panel_width, panel_height), 2)
    
    # Panel title
    font_title = pygame.font.SysFont('Arial', 20, bold=True)
    font_normal = pygame.font.SysFont('Arial', 16)
    
    title = font_title.render("Journey Analysis", True, (0, 0, 0))
    screen.blit(title, (panel_x + 10, panel_y + 10))
    
    # Journey statistics
    total_cost = sum(segment["cost"] for segment in journey_segments)
    walk_segments = sum(1 for segment in journey_segments if segment["action"] == ACTION_WALK)
    boardings = sum(1 for segment in journey_segments if segment["action"] == ACTION_BOARD)
    alightings = sum(1 for segment in journey_segments if segment["action"] == ACTION_ALIGHT)
    transfers = sum(1 for segment in journey_segments if segment["action"] == ACTION_TRANSFER)
    
    y_offset = panel_y + 50
    line_height = 25
    
    stats = [
        f"Total cost: {total_cost}",
        f"Walking segments: {walk_segments}",
        f"Jeepney boardings: {boardings}",
        f"Alightings: {alightings}",
        f"Transfers: {transfers}"
    ]
    
    for stat in stats:
        text = font_normal.render(stat, True, (0, 0, 0))
        screen.blit(text, (panel_x + 15, y_offset))
        y_offset += line_height
    
    # Journey steps
    y_offset += 20
    steps_title = font_title.render("Key Journey Steps:", True, (0, 0, 0))
    screen.blit(steps_title, (panel_x + 10, y_offset))
    y_offset += 30
    
    # Collect key journey events (boarding, transfer, alighting)
    key_events = []
    
    for i, segment in enumerate(journey_segments):
        action = segment["action"]
        
        if action == ACTION_BOARD:
            jeep_id = segment.get("jeep_id", "unknown")
            key_events.append(("Board", f"Jeepney {jeep_id}", jeeps[jeep_id].color if jeep_id < len(jeeps) else (0, 0, 0)))
        
        elif action == ACTION_TRANSFER:
            if "from_jeep" in segment and "to_jeep" in segment:
                from_jeep = segment["from_jeep"]
                to_jeep = segment["to_jeep"]
                key_events.append(("Transfer", f"Jeep {from_jeep} → {to_jeep}", TRANSFER_COLOR))
        
        elif action == ACTION_ALIGHT:
            key_events.append(("Alight", "", ALIGHTING_COLOR))
    
    # Display key events
    for i, (event_type, details, color) in enumerate(key_events):
        if y_offset > panel_y + panel_height - 30:
            # Don't go beyond panel
            more_text = font_normal.render("... more steps not shown", True, (100, 100, 100))
            screen.blit(more_text, (panel_x + 15, y_offset))
            break
            
        # Draw colored circle
        pygame.draw.circle(screen, color, (panel_x + 25, y_offset + 8), 8)
        
        # Draw event text
        event_text = font_normal.render(f"{event_type}: {details}", True, (0, 0, 0))
        screen.blit(event_text, (panel_x + 40, y_offset))
        
        y_offset += line_height

def draw_dashed_line(screen, color, start_pos, end_pos, width=1, dash_length=10):
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    distance = max(1, math.sqrt(dx*dx + dy*dy))
    dash_count = int(distance / dash_length)
    
    if dash_count < 1:
        pygame.draw.line(screen, color, start_pos, end_pos, width)
        return
    
    unit_dx = dx / dash_count
    unit_dy = dy / dash_count
    
    for i in range(0, dash_count, 2):
        start_x = start_pos[0] + unit_dx * i
        start_y = start_pos[1] + unit_dy * i
        end_x = start_pos[0] + unit_dx * (i + 1)
        end_y = start_pos[1] + unit_dy * (i + 1)
        
        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), width)

def draw_point(screen, point, color, size):
    screen_point = grid.get_grid_coors(*point)
    pygame.draw.circle(screen, color, screen_point, size)

if __name__ == "__main__":
    main()