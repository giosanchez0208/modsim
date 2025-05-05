import random
import pygame

class JeepSet:
    COLOR_ORDER = [
        ('ROYAL_BLUE', (110, 115, 209)),
        ('RED',        (252, 35, 20)),
        ('GREEN',      (31, 149, 61)),
        ('PINK',       (248, 167, 200)),
        ('YELLOW',     (248, 193, 38)),
        ('GRAY',       (163, 163, 163)),
    ]

    def __init__(self):
        from jeeproute import JeepRoute
        self.routes = []
        for idx, (name, color) in enumerate(self.COLOR_ORDER):
            route = JeepRoute(color=color)
            route.jeep_id = idx
            self.routes.append(route)

    def __iter__(self):
        return iter(self.routes)

    def __getitem__(self, index):
        return self.routes[index]

    def __len__(self):
        return len(self.routes)

    def add_to_graph(self, travel_graph):
        """Registers all Jeeps in this set into the given TravelGraph."""
        for idx, route in enumerate(self.routes):
            travel_graph.addJeep(route, jeep_id=idx)
    
    def crossover(parent1, parent2):
        def create_child(first_parent, second_parent):
            child = JeepSet()
            
            for i in range(len(child)):
                source = first_parent if i < 3 else second_parent
                child[i].route = [point for point in source[i].route]
                child[i].route_points = [point for point in source[i].route_points]
                child[i].jeep_id = source[i].jeep_id
                
            return child

        return (
            create_child(parent1, parent2),
            create_child(parent2, parent1)
        )

    def mutate(self, shift_range=(-2, 2), specific_jeep_idx=None, visualize_callback=None):
        """
        Mutate a route by shifting one segment while preserving rectangular shape.
        Returns mutation info or None if invalid mutation.
        """
        # Select jeep to mutate
        if specific_jeep_idx is not None and 0 <= specific_jeep_idx < len(self.routes):
            jeep_idx = specific_jeep_idx
        else:
            jeep_idx = random.randrange(len(self.routes))
        
        jeep = self.routes[jeep_idx]
        corners = jeep.route

        if len(corners) < 4:
            return None  # Not enough corners to mutate

        # Pick a random segment
        segment_index = random.randrange(len(corners))
        start_idx = segment_index
        end_idx = (segment_index + 1) % len(corners)
        
        start = corners[start_idx]
        end = corners[end_idx]

        x1, y1 = start
        x2, y2 = end

        is_horizontal = y1 == y2
        is_vertical = x1 == x2

        if not (is_horizontal or is_vertical):
            return None  # Skip diagonal segments

        # Calculate potential shift amount
        min_shift, max_shift = shift_range
        shift = random.randint(min_shift, max_shift)
        if shift == 0:  # Ensure we actually move
            shift = 1 if random.random() > 0.5 else -1
        
        new_corners = corners.copy()
        
        # Apply shift while maintaining rectangular shape
        if is_horizontal:
            new_y = max(0, min(16, y1 + shift))
            # Update all points with the same y-coordinate
            for i, (x, y) in enumerate(corners):
                if y == y1:
                    new_corners[i] = (x, new_y)
        else:
            new_x = max(0, min(16, x1 + shift))
            # Update all points with the same x-coordinate
            for i, (x, y) in enumerate(corners):
                if x == x1:
                    new_corners[i] = (new_x, y)

        # Validate mutation
        valid = True
        segments = set()
        
        for i in range(len(new_corners)):
            p1 = new_corners[i]
            p2 = new_corners[(i + 1) % len(new_corners)]
            
            # Check for diagonal segments
            if p1[0] != p2[0] and p1[1] != p2[1]:
                valid = False
                break
            
            # Check for duplicate segments
            segment = frozenset([p1, p2])
            if segment in segments:
                valid = False
                break
            segments.add(segment)

        if not valid:
            return None

        # Apply valid mutation
        jeep.route = new_corners
        jeep.routeToRoutePoints()

        # Visualization callback if needed
        if visualize_callback:
            visualize_callback(jeep_idx, segment_index, shift, is_horizontal)

        return (jeep_idx, segment_index, shift, is_horizontal)

    def smart_mutate(self, min_attempts=3, max_attempts=10):
        """Try multiple mutations until finding a valid one"""
        attempts = 0
        while attempts < max_attempts:
            result = self.mutate()
            if result is not None:
                return result
            attempts += 1
        return None


# VISUALIZATION FUNCTIONS
# VISUALIZATION FUNCTIONS

def visualize_mutation(screen, jeep_set, jeep_idx, segment_idx, shift, is_horizontal,
                       original_color=(100, 100, 100), mutated_color=(255, 0, 0),
                       grid_func=None, get_grid_coors_func=None):
    """Visualize a mutation on the screen"""
    if grid_func:
        grid_func(screen)
        
    if get_grid_coors_func is None:
        # Default grid coordinate conversion
        def get_grid_coors_default(x, y):
            grid_size = min(screen.get_width(), screen.get_height()) / 20
            return (int(x * grid_size + grid_size), int(y * grid_size + grid_size))
        get_grid_coors_func = get_grid_coors_default
    
    # Draw mutated route
    jeep = jeep_set[jeep_idx]
    route_points = [get_grid_coors_func(*p) for p in jeep.route_points]
    
    if len(route_points) > 1:
        pygame.draw.lines(screen, mutated_color, True, route_points, 3)
        
        # Highlight mutated segment
        start_point = jeep.route[segment_idx]
        end_point = jeep.route[(segment_idx + 1) % len(jeep.route)]
        start_screen = get_grid_coors_func(*start_point)
        end_screen = get_grid_coors_func(*end_point)
        
        pygame.draw.line(screen, (255, 255, 0), start_screen, end_screen, 5)
        pygame.draw.circle(screen, (0, 0, 255), start_screen, 8)
        pygame.draw.circle(screen, (0, 255, 0), end_screen, 8)
        
        # Show mutation info
        font = pygame.font.Font(None, 24)
        info_text = f"Jeep {jeep_idx}, {'Horizontal' if is_horizontal else 'Vertical'} Shift: {shift}"
        text_surface = font.render(info_text, True, (0, 0, 0))
        screen.blit(text_surface, (10, screen.get_height() - 30))

# SIMPLIFIED TEST MODE

def enhanced_test_mode():
    """Test mode with basic visualization"""
    import pygame
    import sys
    from grid import SCREEN_WIDTH, SCREEN_HEIGHT, draw_grid, get_grid_coors
    
    # Pygame setup
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Jeep Route Mutation Visualizer")
    
    # Create jeep set
    jeep_set = JeepSet()
    
    # Visualization state
    current_mutation = None
    show_route_points = True
    clock = pygame.time.Clock()
    
    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    current_mutation = jeep_set.smart_mutate()
                elif event.key == pygame.K_r:  # Reset routes
                    jeep_set = JeepSet()
                    current_mutation = None
                elif event.key == pygame.K_p:  # Toggle points
                    show_route_points = not show_route_points
                elif pygame.K_1 <= event.key <= pygame.K_6:  # Number keys 1-6
                    jeep_idx = event.key - pygame.K_1
                    current_mutation = jeep_set.mutate(specific_jeep_idx=jeep_idx)

        # Draw everything
        screen.fill((255, 255, 255))
        draw_grid(screen)

        # Draw all jeep routes
        for jeep in jeep_set:
            points = [get_grid_coors(*p) for p in jeep.route_points]
            if len(points) > 1:
                pygame.draw.lines(screen, jeep.color, True, points, 3)
            
            # Draw corner points
            for point in jeep.route:
                pos = get_grid_coors(*point)
                pygame.draw.circle(screen, (0, 0, 0), pos, 5)
            
            # Draw route points if enabled
            if show_route_points:
                for point in jeep.route_points:
                    pos = get_grid_coors(*point)
                    pygame.draw.circle(screen, (200, 200, 200), pos, 2)

        # Draw mutation visualization if exists
        if current_mutation:
            visualize_mutation(screen, jeep_set, *current_mutation,
                               grid_func=None, get_grid_coors_func=get_grid_coors)

        # Draw controls help
        font = pygame.font.Font(None, 24)
        controls = [
            "SPACE: Random mutation",
            "1-6: Mutate specific jeep",
            "R: Reset all routes",
            "P: Toggle route points"
        ]
        for i, text in enumerate(controls):
            text_surface = font.render(text, True, (0, 0, 0))
            screen.blit(text_surface, (10, 10 + i * 25))

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    enhanced_test_mode()