from random import randint
import pygame
import grid
import math

# Constants moved to top level for better visibility and maintenance
JEEP_SPEED = 150
SLOWDOWN_FACTOR = 0.3
SPEED_RECOVERY_RATE = 0.8
MAX_CAPACITY = 16

class JeepRoute:
    def __init__(self, color=(255, 0, 0), route=None, route_points=None):
        # JEEPNEY ROUTE INITIALIZATION
        self.color = color
        self.route = [] if route is None else route
        self.route_points = [] if route_points is None else route_points
        
        if not self.route:
            self.randomizeRoute()
            
        if len(self.route_points) < 2:
            raise ValueError("Route must have at least 2 points")
            
        # JEEPNEYS INITIALIZATION
        self._initialize_jeeps()
        
        # Speed properties
        self.speed = JEEP_SPEED
        self.current_speed = [JEEP_SPEED, JEEP_SPEED]
        self.last_passenger_count = [0, 0]
        
        # PASSENGER INITIALIZATION
        self.MAX_CAPACITY = MAX_CAPACITY
        self.passengerAmt = [0, 0]

    def _initialize_jeeps(self):
        """Initialize jeep properties and positions"""
        self.isMovingAlongX = [False, False]
        self.isInReverse = [False, False]
        
        # Initialize position tracking variables
        self.jeepLocation = [None, None]
        self.exact_position = [None, None]
        self.jeepDestination = [None, None]
        self.current_route_index = [None, None]
        
        # Place first jeep at random location on route
        startIndex = randint(0, len(self.route_points) - 1)
        self.current_route_index[0] = startIndex
        self.jeepLocation[0] = grid.get_grid_coors(*self.route_points[startIndex])
        self.exact_position[0] = list(self.jeepLocation[0])
        
        # Place second jeep at halfway point on route
        route_length = len(self.route_points)
        half_way_index = (startIndex + route_length // 2) % route_length
        self.current_route_index[1] = half_way_index
        self.jeepLocation[1] = grid.get_grid_coors(*self.route_points[half_way_index])
        self.exact_position[1] = list(self.jeepLocation[1])
        
        # Set initial destinations for both jeeps
        for i in range(2):
            next_index = (self.current_route_index[i] + 1) % len(self.route_points)
            self.jeepDestination[i] = grid.get_grid_coors(*self.route_points[next_index])
        
    def randomizeRoute(self): 
        """Generate a random route for jeepneys to follow"""
        self.route = []
        self.route_points = []
        turns = randint(1, 3)
        
        # Start with a random point
        start_point = (randint(0, 16), randint(0, 16))
        self.route.append(start_point)
        self.route_points.append(start_point)
        
        # Keep track of all points to avoid duplicates
        all_points = {start_point}
        
        # Generate a random route with turns
        for _ in range(turns):
            prev_x, prev_y = self.route[-1]
            
            # Find a new x coordinate
            new_x = self._find_new_coordinate(prev_x, prev_y, True, all_points)
            
            # Find a new y coordinate
            new_y = self._find_new_coordinate(new_x, prev_y, False, all_points)
            
        # Complete the route by connecting back to the start point
        self._complete_route_loop(all_points)
    
    def _find_new_coordinate(self, prev_x, prev_y, is_x_direction, all_points):
        """Find a new coordinate in either x or y direction"""
        attempts = 0
        max_attempts = 100
        
        if is_x_direction:
            # Find a new x coordinate
            while attempts < max_attempts:
                new_x = randint(0, 16)
                if new_x != prev_x:
                    path_clear = True
                    step = 1 if new_x > prev_x else -1
                    
                    # Check if path is clear
                    for x in range(prev_x + step, new_x + step, step):
                        if (x, prev_y) in self.route_points:
                            path_clear = False
                            break
                    
                    if path_clear:
                        # Add horizontal path points
                        for x in range(prev_x + step, new_x + step, step):
                            point = (x, prev_y)
                            if point not in all_points:
                                self.route_points.append(point)
                                all_points.add(point)
                        self.route.append((new_x, prev_y))
                        return new_x
                attempts += 1
            return prev_x  # Return original coordinate if we couldn't find a valid new one
        else:
            # Find a new y coordinate
            while attempts < max_attempts:
                new_y = randint(0, 16)
                if new_y != prev_y:
                    path_clear = True
                    step = 1 if new_y > prev_y else -1
                    
                    # Check if path is clear
                    for y in range(prev_y + step, new_y + step, step):
                        if (prev_x, y) in self.route_points:
                            path_clear = False
                            break
                    
                    if path_clear:
                        # Add vertical path points
                        for y in range(prev_y + step, new_y + step, step):
                            point = (prev_x, y)
                            if point not in all_points:
                                self.route_points.append(point)
                                all_points.add(point)
                        self.route.append((prev_x, new_y))
                        return new_y
                attempts += 1
            return prev_y  # Return original coordinate if we couldn't find a valid new one
    
    def _complete_route_loop(self, all_points):
        """Connect the route back to its starting point"""
        first_x, first_y = self.route[0]
        last_x, last_y = self.route[-1]
        
        # Move horizontally to match the first x-coordinate
        if first_x != last_x:
            step = 1 if first_x > last_x else -1
            for x in range(last_x + step, first_x + step, step):
                point = (x, last_y)
                if point not in all_points:
                    self.route_points.append(point)
                    all_points.add(point)
            self.route.append((first_x, last_y))
        
        # Move vertically to match the first y-coordinate
        if first_y != last_y or first_x != last_x:
            step = 1 if first_y > last_y else -1
            for y in range(last_y + step, first_y + step, step):
                point = (first_x, y)
                if point not in all_points:
                    self.route_points.append(point)
                    all_points.add(point)
            self.route.append((first_x, first_y))
    
    def routeToRoutePoints(self):
        """Convert route corners to a list of all grid points on the route"""
        self.route_points = []
        if not self.route or len(self.route) < 2:
            return

        for i in range(len(self.route)):
            x1, y1 = self.route[i]
            x2, y2 = self.route[(i + 1) % len(self.route)]  # wrap around

            if x1 == x2:
                # Vertical segment
                step = 1 if y2 > y1 else -1
                for y in range(y1, y2 + step, step):
                    self.route_points.append((x1, y))
            elif y1 == y2:
                # Horizontal segment
                step = 1 if x2 > x1 else -1
                for x in range(x1, x2 + step, step):
                    self.route_points.append((x, y1))
        # Remove duplicate consecutive points
        self.route_points = [pt for i, pt in enumerate(self.route_points)
                            if i == 0 or pt != self.route_points[i - 1]]
    
    def drawRoute(self, screen):
        """Draw the route on the screen"""
        screen_points = [grid.get_grid_coors(x, y) for x, y in self.route]
        pygame.draw.polygon(screen, self.color, screen_points, 5)
        
    def drawJeep(self, screen):
        """Draw both jeeps on the screen with passengers"""
        for jeep_id in range(2):
            jeep_x, jeep_y = self.jeepLocation[jeep_id][0], self.jeepLocation[jeep_id][1]
            
            # Scale jeep to 2/3 size: original (68, 20) -> (45, 13)
            jeep_surface = pygame.Surface((45, 13), pygame.SRCALPHA)
            jeep_surface.fill(self.color)

            # Draw passengers
            self._draw_passengers(jeep_surface, jeep_id)

            # Calculate rotation angle based on movement direction
            angle = self._calculate_jeep_angle(jeep_id)

            rotated_surface = pygame.transform.rotate(jeep_surface, angle)
            screen.blit(rotated_surface, (jeep_x - rotated_surface.get_width() // 2, 
                                         jeep_y - rotated_surface.get_height() // 2))
    
    def _draw_passengers(self, jeep_surface, jeep_id):
        """Draw passengers inside the jeep"""
        passenger_count = min(self.passengerAmt[jeep_id], self.MAX_CAPACITY)
        
        for i in range(passenger_count):
            # Scale passenger square to 2/3 size: original (5, 5) -> (3, 3)
            square_surface = pygame.Surface((3, 3))
            square_surface.fill((96, 96, 96))
            
            if i < 8:
                x_offset = 3 + i * 5  # 2/3 of original offset and spacing
                y_offset = 2
            else:
                x_offset = 3 + (i - 8) * 5
                y_offset = jeep_surface.get_height() - 5

            jeep_surface.blit(square_surface, (x_offset, y_offset))
    
    def _calculate_jeep_angle(self, jeep_id):
        """Calculate the rotation angle of the jeep based on movement direction"""
        if self.isMovingAlongX[jeep_id] and self.isInReverse[jeep_id]:
            return 0
        if self.isMovingAlongX[jeep_id] and not self.isInReverse[jeep_id]:
            return 180
        if not self.isMovingAlongX[jeep_id] and not self.isInReverse[jeep_id]:
            return 90
        # not self.isMovingAlongX[jeep_id] and self.isInReverse[jeep_id]
        return 270

    def getPassengerAmt(self, jeep_id=0):
        """Get the number of passengers in a jeep"""
        return self.passengerAmt[jeep_id]
        
    def modifyPassenger(self, amt=1, jeep_id=0):
        """Add or remove passengers from a jeep"""
        self.passengerAmt[jeep_id] += amt

    def update(self, dt):
        """Update jeep positions and handle speed adjustments"""
        for jeep_id in range(2):
            # Check for passenger changes and adjust speed
            self._update_jeep_speed(jeep_id, dt)
            
            # Update jeep position
            self._update_jeep_position(jeep_id, dt)
    
    def _update_jeep_speed(self, jeep_id, dt):
        """Maintain a consistent jeep speed"""
        self.current_speed[jeep_id] = JEEP_SPEED
        
    def _update_jeep_position(self, jeep_id, dt):
        """Update jeep position based on current destination"""
        dx = self.jeepDestination[jeep_id][0] - self.exact_position[jeep_id][0]
        dy = self.jeepDestination[jeep_id][1] - self.exact_position[jeep_id][1]
        distance = math.sqrt(dx * dx + dy * dy)

        # Check if jeep reached destination
        if distance < 2:
            self._set_new_destination(jeep_id)
        else:
            self._move_jeep(jeep_id, dx, dy, dt)
    
    def _set_new_destination(self, jeep_id):
        """Set jeep to current destination and determine next destination"""
        # Snap to exact destination position
        self.exact_position[jeep_id][0] = self.jeepDestination[jeep_id][0]
        self.exact_position[jeep_id][1] = self.jeepDestination[jeep_id][1]
        self.jeepLocation[jeep_id] = (int(self.exact_position[jeep_id][0]),
                                      int(self.exact_position[jeep_id][1]))

        # Move to next point in route
        self.current_route_index[jeep_id] = (self.current_route_index[jeep_id] + 1) % len(self.route_points)
        next_index = (self.current_route_index[jeep_id] + 1) % len(self.route_points)
        self.jeepDestination[jeep_id] = grid.get_grid_coors(*self.route_points[next_index])
    
    def _move_jeep(self, jeep_id, dx, dy, dt):
        """Move jeep toward destination"""
        if abs(dx) > abs(dy):
            # Move horizontally
            move_distance = min(self.current_speed[jeep_id] * dt, abs(dx))
            self.exact_position[jeep_id][0] += math.copysign(move_distance, dx)
            self.isMovingAlongX[jeep_id] = True
            self.isInReverse[jeep_id] = dx < 0
        else:
            # Move vertically
            move_distance = min(self.current_speed[jeep_id] * dt, abs(dy))
            self.exact_position[jeep_id][1] += math.copysign(move_distance, dy)
            self.isMovingAlongX[jeep_id] = False
            self.isInReverse[jeep_id] = dy < 0

        # Update grid-aligned location
        self.jeepLocation[jeep_id] = (int(self.exact_position[jeep_id][0]),
                                      int(self.exact_position[jeep_id][1]))
