import pygame
import random
import grid
import math

# Initialize pygame font module
pygame.font.init()

# Color Constants
AREA_COLOR = (206, 195, 188)
PIN_COLOR = (51, 51, 51)
PIN_TEXT_COLOR = (240, 235, 231)
futuraltheavy_font = pygame.font.Font('FUTURALT-HEAVY.TTF', 10)

# Helper function to draw waiting pins at any grid position
def draw_waiting_pin(screen, screen_position, count, font, color=PIN_COLOR):
    """Draw a pin showing the number of waiting passengers at any position."""
    if count <= 0:
        return

    # Pin position (slightly above the position)
    pin_x, pin_y = screen_position
    pin_y -= 30  # Offset above the node

    # Draw the circle part of the pin
    pygame.draw.circle(screen, color, (pin_x, pin_y), 7)  # 15px diameter

    # Draw the triangle part (pointing downward)
    triangle_points = [
        (pin_x - 6, pin_y),   # 1px thinner on each side
        (pin_x + 6, pin_y),
        (pin_x, pin_y + 15)
    ]
    pygame.draw.polygon(screen, color, triangle_points)

    # Render the waiting count text
    text_surface = font.render(str(count), True, PIN_TEXT_COLOR)
    text_rect = text_surface.get_rect(center=(pin_x, pin_y))
    # Nudge: one down (y+1), twice to the left (x-2)
    text_rect.centerx -= 0.4
    text_rect.centery -= 0
    screen.blit(text_surface, text_rect)

class Area:
    def __init__(self, grid_position):
        self.grid_position = grid_position  # (x, y) in grid coordinates
        self.screen_position = grid.get_grid_coors(*grid_position)  # (x, y) in screen coordinates
        self.waiting_passengers = 0  # Count of passengers waiting at this area
    
    def update_waiting_count(self, count):
        self.waiting_passengers = count

    def draw_waiting_pin(self, screen, font):
        """Draw a pin showing the number of waiting passengers."""
        if self.waiting_passengers <= 0:
            return
        
        # Use the global helper function
        draw_waiting_pin(screen, self.screen_position, self.waiting_passengers, font)

class ResidentialArea(Area):
    def __init__(self, grid_position):
        super().__init__(grid_position)
    
    def draw(self, screen):
        """Draw a triangle representing a residential area."""
        side_length = 15
        height = math.sqrt(3) * side_length / 2
        
        x, y = self.screen_position
        top_point = (x, y - height * 2/3)
        bottom_left = (x - side_length/2, y + height/3)
        bottom_right = (x + side_length/2, y + height/3)
        
        pygame.draw.polygon(screen, AREA_COLOR, [top_point, bottom_left, bottom_right], 3)

class NonResidentialArea(Area):
    def __init__(self, grid_position):
        super().__init__(grid_position)
    
    def draw(self, screen):
        """Draw a circle representing a non-residential area."""
        # Draw the circle with no fill and a stroke
        pygame.draw.circle(screen, AREA_COLOR, self.screen_position, 7.5, 3)

class AreaManager:
    def __init__(self, grid_size=17):
        self.grid_size = grid_size
        self.residential_areas = []
        self.non_residential_areas = []
        self.all_areas = {}  # Dictionary mapping grid positions to area objects
        self.font = futuraltheavy_font
    
    def add_residential_area(self, grid_position):
        area = ResidentialArea(grid_position)
        self.residential_areas.append(area)
        self.all_areas[grid_position] = area
        return area

    def add_non_residential_area(self, grid_position):
        area = NonResidentialArea(grid_position)
        self.non_residential_areas.append(area)
        self.all_areas[grid_position] = area
        return area

    def generate_random_areas(self, num_residential=5, num_non_residential=5):
        self.clear_areas()
        
        available_positions = [(x, y) for x in range(self.grid_size) for y in range(self.grid_size)]
        random.shuffle(available_positions)
        
        for i in range(min(num_residential, len(available_positions))):
            self.add_residential_area(available_positions[i])
        
        for i in range(num_residential, min(num_residential + num_non_residential, len(available_positions))):
            self.add_non_residential_area(available_positions[i])

    def define_areas(self, residential_positions, non_residential_positions):
        self.clear_areas()
        
        for pos in residential_positions:
            self.add_residential_area(pos)
            
        for pos in non_residential_positions:
            self.add_non_residential_area(pos)

    def clear_areas(self):
        self.residential_areas = []
        self.non_residential_areas = []
        self.all_areas = {}

    def get_random_origin_destination_pair(self):
        if random.random() < 0.5:
            if not self.residential_areas or not self.non_residential_areas:
                return None, None
            origin = random.choice(self.residential_areas).grid_position
            destination = random.choice(self.non_residential_areas).grid_position
        else:
            if not self.residential_areas or not self.non_residential_areas:
                return None, None
            origin = random.choice(self.non_residential_areas).grid_position
            destination = random.choice(self.residential_areas).grid_position
        
        return origin, destination

    def update_waiting_count(self, grid_position, count):
        if grid_position in self.all_areas:
            self.all_areas[grid_position].update_waiting_count(count)

    def get_waiting_pins(self):
        waiting_pins = {}
        for pos, area in self.all_areas.items():
            if area.waiting_passengers > 0:
                waiting_pins[pos] = area.waiting_passengers
        return waiting_pins

    def draw(self, screen):
        for area in self.residential_areas + self.non_residential_areas:
            area.draw(screen)