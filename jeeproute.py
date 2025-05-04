from random import randint
import pygame
import grid
import math

JEEP_SPEED = 150
class JeepRoute:
    def __init__(self, color=(255, 0, 0), route=None, route_points=None):
        # JEEPNEY ROUTE ============================================================
        self.color = color
        self.route = [] if route is None else route
        self.route_points = [] if route_points is None else route_points
        
        if not self.route:
            self.randomizeRoute()
            
        # JEEPNEYS =================================================================
        self.isMovingAlongX = [False, False]
        self.isInReverse = [False, False]
        
        if len(self.route_points) < 2:
            raise ValueError("Route must have at least 2 points")
            
        # Initialize both jeeps
        self.jeepLocation = [None, None]
        self.exact_position = [None, None]
        self.jeepDestination = [None, None]
        self.current_route_index = [None, None]
        
        # Put first jeep on random location
        startIndex = randint(0, len(self.route_points) - 1)
        self.current_route_index[0] = startIndex
        self.jeepLocation[0] = grid.get_grid_coors(*self.route_points[startIndex])
        self.exact_position[0] = list(self.jeepLocation[0])
        
        # Calculate half-way index safely
        route_length = len(self.route_points)
        half_way_index = (startIndex + route_length // 2) % route_length
        self.current_route_index[1] = half_way_index
        self.jeepLocation[1] = grid.get_grid_coors(*self.route_points[half_way_index])
        self.exact_position[1] = list(self.jeepLocation[1])
        
        # Set initial destinations for both jeeps
        for i in range(2):
            next_index = (self.current_route_index[i] + 1) % len(self.route_points)
            self.jeepDestination[i] = grid.get_grid_coors(*self.route_points[next_index])
        
        self.speed = JEEP_SPEED
        
        # PASSENGER ================================================================
        self.MAX_CAPACITY = 16
        self.passengerAmt = [0, 0]

        
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
        for jeep_id in range(2):  # Draw both jeeps
            jeep_x, jeep_y = self.jeepLocation[jeep_id][0], self.jeepLocation[jeep_id][1]
            
            # Scale jeep to 2/3 size: original (68, 20) -> (45, 13)
            jeep_surface = pygame.Surface((45, 13), pygame.SRCALPHA)
            jeep_surface.fill(self.color)

            passenger_count = min(self.passengerAmt[jeep_id], 16)
            
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

            dx = self.jeepDestination[jeep_id][0] - self.exact_position[jeep_id][0]
            dy = self.jeepDestination[jeep_id][1] - self.exact_position[jeep_id][1]

            if self.isMovingAlongX[jeep_id] and self.isInReverse[jeep_id]:
                angle = 0
            if self.isMovingAlongX[jeep_id] and not self.isInReverse[jeep_id]:
                angle = 180
            if not self.isMovingAlongX[jeep_id] and not self.isInReverse[jeep_id]:
                angle = 90
            if not self.isMovingAlongX[jeep_id] and self.isInReverse[jeep_id]:
                angle = 270

            rotated_surface = pygame.transform.rotate(jeep_surface, angle)
            screen.blit(rotated_surface, (jeep_x - rotated_surface.get_width() // 2, 
                                         jeep_y - rotated_surface.get_height() // 2))

    def getPassengerAmt(self, jeep_id=0):
        return self.passengerAmt[jeep_id]
        
    def modifyPassenger(self, amt=1, jeep_id=0):
        self.passengerAmt[jeep_id] += amt

    def update(self, dt):
        for jeep_id in range(2):  # Update both jeeps
            dx = self.jeepDestination[jeep_id][0] - self.exact_position[jeep_id][0]
            dy = self.jeepDestination[jeep_id][1] - self.exact_position[jeep_id][1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 2:
                self.exact_position[jeep_id][0] = self.jeepDestination[jeep_id][0]
                self.exact_position[jeep_id][1] = self.jeepDestination[jeep_id][1]
                self.jeepLocation[jeep_id] = (int(self.exact_position[jeep_id][0]), 
                                             int(self.exact_position[jeep_id][1]))
                
                self.current_route_index[jeep_id] = (self.current_route_index[jeep_id] + 1) % len(self.route_points)
                next_index = (self.current_route_index[jeep_id] + 1) % len(self.route_points)
                self.jeepDestination[jeep_id] = grid.get_grid_coors(*self.route_points[next_index])
                
            else:
                if abs(dx) > abs(dy):
                    move_distance = min(self.speed * dt, abs(dx))
                    self.exact_position[jeep_id][0] += math.copysign(move_distance, dx)
                    self.isMovingAlongX[jeep_id] = True
                    self.isInReverse[jeep_id] = dx < 0
                else:
                    move_distance = min(self.speed * dt, abs(dy))
                    self.exact_position[jeep_id][1] += math.copysign(move_distance, dy)
                    self.isMovingAlongX[jeep_id] = False
                    self.isInReverse[jeep_id] = dy < 0
                    
                self.jeepLocation[jeep_id] = (int(self.exact_position[jeep_id][0]), 
                                             int(self.exact_position[jeep_id][1]))