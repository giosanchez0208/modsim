from random import randint
import pygame
import grid
import math

class JeepRoute:
    def __init__(self, color=(255, 0, 0), route=None, route_points=None):
        
        # JEEPNEY ROUTE ============================================================
        
        # Store the route color
        self.color = color
        
        # Initialize empty lists for route and route_points
        self.route = [] if route is None else route
        self.route_points = [] if route_points is None else route_points
        
        # Generate a random route if none was provided
        if not self.route:
            self.randomizeRoute()
            
        # JEEPNEY ===================================================================

        # Orientation
        self.isMovingAlongX = False
        self.isInReverse = False
        
        # Ensure there are points to work with
        if len(self.route_points) < 2:
            raise ValueError("Route must have at least 2 points")
            
        # Put jeep on random location
        startIndex = randint(0, len(self.route_points) - 1)
        self.jeepLocation = grid.get_grid_coors(*self.route_points[startIndex])
        
        # Store the current route point index to track position
        self.current_route_index = startIndex
        
        # Set the initial destination
        next_index = (startIndex + 1) % len(self.route_points)
        self.jeepDestination = grid.get_grid_coors(*self.route_points[next_index])
        
        # Movement speed (pixels per second)
        self.speed = 100
        
        # Track exact position with floating point values for smoother movement
        self.exact_position = list(self.jeepLocation)
        
        # PASSENGER ================================================================
        
        self.passengerAmt = 0
        
    def randomizeRoute(self): 
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
            
            # Find a new x coor, make a new point with that coordinate.
            attempts = 0
            while attempts < 100: 
                new_x = randint(0, 16)
                if new_x != prev_x: 
                    path_clear = True
                    step = 1 if new_x > prev_x else -1
                    for x in range(prev_x + step, new_x + step, step):
                        if (x, prev_y) in self.route_points:
                            path_clear = False
                            break
                    
                    if path_clear:
                        # Add the horizontal path points
                        for x in range(prev_x + step, new_x + step, step):
                            point = (x, prev_y)
                            if point not in all_points:
                                self.route_points.append(point)
                                all_points.add(point)
                        self.route.append((new_x, prev_y))
                        break
                attempts += 1
            if attempts >= 100:
                new_x = prev_x
            
            # Find a new y coor, make a new point with that coordinate and the new x coordinate.
            attempts = 0
            while attempts < 100:
                new_y = randint(0, 16)
                if new_y != prev_y:
                    path_clear = True
                    step = 1 if new_y > prev_y else -1
                    for y in range(prev_y + step, new_y + step, step):
                        if (new_x, y) in self.route_points:
                            path_clear = False
                            break
                    
                    if path_clear:
                        for y in range(prev_y + step, new_y + step, step):
                            point = (new_x, y)
                            if point not in all_points:
                                self.route_points.append(point)
                                all_points.add(point)
                        self.route.append((new_x, new_y))
                        break
                attempts += 1
            
        # Complete the route by connecting back to the start x-coordinate
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
    
    def drawRoute(self, screen):
        screen_points = [grid.get_grid_coors(x, y) for x, y in self.route]
        pygame.draw.polygon(screen, self.color, screen_points, 5)
        
    def drawJeep(self, screen):
        jeep_x, jeep_y = self.jeepLocation[0], self.jeepLocation[1]
        
        # Create a base surface (assume default horizontal orientation)
        jeep_surface = pygame.Surface((68, 20))
        jeep_surface.fill(self.color)

        # Draw self.passengerAmt number of squares
        passenger_count = min(self.passengerAmt, 16)

        # Create a surface for each passenger and position them
        for i in range(passenger_count):
            square_surface = pygame.Surface((5, 5))
            square_surface.fill((96, 96, 96))  # Color #606060

            if i < 8:
            # Top row passengers
                x_offset = 3 + i * 8  # Spaced 8 pixels apart
                y_offset = 3
            else:
                # Bottom row passengers
                x_offset = 3 + (i - 8) * 8  # Spaced 8 pixels apart
                y_offset = jeep_surface.get_height() - 8  # 3px from bottom

            jeep_surface.blit(square_surface, (x_offset, y_offset))

        # Calculate direction vector
        dx = self.jeepDestination[0] - self.exact_position[0]
        dy = self.jeepDestination[1] - self.exact_position[1]

        # Determine rotation angle (clockwise, based on intended direction)
        if abs(dx) > abs(dy):  # Horizontal movement
            if dx > 0:
                angle = 180 # Right
            else:
                angle = 0 # Left
        else:  # Vertical movement
            if dy > 0:
                angle = 90 # Down
            else:
                angle = 270 # Up

        # Apply rotation
        rotated_surface = pygame.transform.rotate(jeep_surface, angle)

        # Draw the rotated jeep centered on its position
        screen.blit(rotated_surface, (jeep_x - rotated_surface.get_width() // 2, jeep_y - rotated_surface.get_height() // 2))

    def getPassengerAmt(self):
        return self.passengerAmt
        
    def modifyPassenger(self, amt = 1):
        self.passengerAmt += amt

    def update(self, dt):
        # Calculate direction vector and distance to destination
        dx = self.jeepDestination[0] - self.exact_position[0]
        dy = self.jeepDestination[1] - self.exact_position[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # If we're at the destination or very close to it
        if distance < 2:
            # Update the exact position to match the destination
            self.exact_position[0] = self.jeepDestination[0]
            self.exact_position[1] = self.jeepDestination[1]
            self.jeepLocation = (int(self.exact_position[0]), int(self.exact_position[1]))
            
            # Update the destination to the next route point
            self.current_route_index = (self.current_route_index + 1) % len(self.route_points)
            next_index = (self.current_route_index + 1) % len(self.route_points)
            self.jeepDestination = grid.get_grid_coors(*self.route_points[next_index])
            
        else:
            # Move only horizontally or vertically
            if abs(dx) > abs(dy):
                # Move horizontally
                move_distance = min(self.speed * dt, abs(dx))
                self.exact_position[0] += math.copysign(move_distance, dx)
                self.isMovingAlongX = True
                self.isInReverse = dx < 0  # Moving right to left
            else:
                # Move vertically
                move_distance = min(self.speed * dt, abs(dy))
                self.exact_position[1] += math.copysign(move_distance, dy)
                self.isMovingAlongX = False
                self.isInReverse = dy < 0  # Moving bottom to top
                
            # Update the integer position
            self.jeepLocation = (int(self.exact_position[0]), int(self.exact_position[1]))