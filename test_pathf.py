import pygame
import sys
import random
import math
from jeeproute import JeepRoute
from passenger import TravelGraph
import grid

# Initialize pygame
pygame.init()

# Set up the screen
screen = pygame.display.set_mode((grid.SCREEN_WIDTH, grid.SCREEN_HEIGHT))
pygame.display.set_caption("Pathfinding Test")
clock = pygame.time.Clock()

# Define some colors
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

# Path colors
WALKING_COLOR = (100, 100, 100)  # Gray for walking
RIDING_COLORS = {}  # Will be filled with jeep route colors

def generate_test_case():

    num_jeeps = random.randint(2, 5)
    
    jeeps = []
    for i in range(num_jeeps):
        color = JEEP_COLORS[i % len(JEEP_COLORS)] #randomize colors
        jeep = JeepRoute(color=color)
        jeeps.append(jeep)
    
    # Set up the travel graph
    travel_graph = TravelGraph()
    
    # Add all jeeps to the travel graph and store route points for later
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
    
    # Generate random start and end points
    # Make sure they're not on the same spot
    while True:
        start_x, start_y = random.randint(0, 16), random.randint(0, 16)
        end_x, end_y = random.randint(0, 16), random.randint(0, 16)
        if (start_x, start_y) != (end_x, end_y):
            break
    
    start_point = (start_x, start_y)
    end_point = (end_x, end_y)
    
    # Find the shortest path
    cost, path = travel_graph.find_shortest_path(start_point, end_point)
    
    print(f"Generated {num_jeeps} jeep routes")
    print(f"Path found from {start_point} to {end_point}")
    print(f"Total cost: {cost}")
    print(f"Path length: {len(path)} points")
    
    return jeeps, path, start_point, end_point, all_route_points

def main():
    # Generate initial test case
    jeeps, path, start_point, end_point, all_route_points = generate_test_case()
    
    # Instructions text
    font = pygame.font.SysFont('Arial', 24)
    instructions = font.render('Press SPACE to generate a new test case, ESC to quit', True, (0, 0, 0))
    
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
                    jeeps, path, start_point, end_point, all_route_points = generate_test_case()
        
        # Draw everything
        grid.draw_grid(screen)
        
        # Draw instructions
        screen.blit(instructions, (50, 20))
        
        # Draw jeep routes first (background)
        for jeep in jeeps:
            jeep.drawRoute(screen)
        
        # Draw direction arrows next
        for jeep in jeeps:
            draw_route_arrows(screen, jeep)
        
        # Draw path with different colors for walking and riding (on top of jeep routes)
        draw_path(screen, path, all_route_points, jeeps)
        
        # Draw start and end points (always on top)
        draw_point(screen, start_point, (0, 255, 0), 10)  # Green for start
        draw_point(screen, end_point, (255, 0, 255), 10)  # Magenta for end
        
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

def draw_path(screen, path, all_route_points, jeeps):
    if not path or len(path) < 2:
        return
    
    # Convert grid coordinates to screen coordinates
    screen_points = [grid.get_grid_coors(x, y) for x, y in path]
    
    # Draw segments of the path with different colors based on transport mode
    for i in range(len(path) - 1):
        start_point = path[i]
        end_point = path[i + 1]
        
        # Get screen coordinates
        start_screen = screen_points[i]
        end_screen = screen_points[i + 1]
        
        # Determine if this segment is walking or riding
        # We're riding if both points are on the same jeep route
        is_riding = False
        riding_jeep_idx = None
        
        # Check if both points are on jeep routes
        if start_point in all_route_points and end_point in all_route_points:
            # Find common jeep routes
            start_jeeps = set(all_route_points[start_point])
            end_jeeps = set(all_route_points[end_point])
            common_jeeps = start_jeeps.intersection(end_jeeps)
            
            if common_jeeps:
                # Check if they're adjacent on the same jeep route
                jeep_idx = next(iter(common_jeeps))
                route_points = jeeps[jeep_idx].route_points
                
                # Find indices of start and end in route_points
                try:
                    s_idx = route_points.index(start_point)
                    e_idx = route_points.index(end_point)
                    
                    # Check if they're adjacent or wrap around
                    if e_idx == (s_idx + 1) % len(route_points) or s_idx == (e_idx + 1) % len(route_points):
                        is_riding = True
                        riding_jeep_idx = jeep_idx
                except ValueError:
                    pass  # Not found in route_points
        
        # Draw the line segment with appropriate color
        if is_riding:
            color = jeeps[riding_jeep_idx].color
            # Draw a much thicker line for riding to make it more visible
            line_width = 8
            # Draw a slightly transparent background line to help it stand out
            pygame.draw.line(screen, (255, 255, 255), start_screen, end_screen, line_width + 4)
            # Draw the colored line on top
            pygame.draw.line(screen, color, start_screen, end_screen, line_width)
            
            # Draw a small circle to indicate jeep stop
            pygame.draw.circle(screen, (255, 255, 255), start_screen, 9)  # White outline
            pygame.draw.circle(screen, color, start_screen, 7)
            # For the last point in the path
            if i == len(path) - 2:
                pygame.draw.circle(screen, (255, 255, 255), end_screen, 9)  # White outline
                pygame.draw.circle(screen, color, end_screen, 7)
        else:
            # Walking segment - dashed line
            line_width = 3
            # Draw a white background for better visibility
            draw_dashed_line(screen, (255, 255, 255), start_screen, end_screen, line_width + 2)
            # Draw the actual dashed line
            draw_dashed_line(screen, WALKING_COLOR, start_screen, end_screen, line_width)
    
    # Draw way points (nodes along the path that aren't start/end points)
    for i in range(1, len(screen_points) - 1):
        point = path[i]
        screen_point = screen_points[i]
        
        # Different circle for points on jeep routes
        if point in all_route_points:
            # Find which jeep(s) this point belongs to
            jeep_indices = all_route_points[point]
            if jeep_indices:
                # Use the color of the first jeep it belongs to
                color = jeeps[jeep_indices[0]].color
                pygame.draw.circle(screen, color, screen_point, 6)
        else:
            # Regular waypoint (walking)
            pygame.draw.circle(screen, WALKING_COLOR, screen_point, 4)

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