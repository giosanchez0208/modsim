import pygame
import sys
import math
from grid import SCREEN_WIDTH, SCREEN_HEIGHT, draw_grid, get_grid_coors
from jeeproute import JeepRoute
from passenger import Passenger, TravelGraph
from areas import AreaManager, draw_waiting_pin
from jeepset import JeepSet
import csv
from datetime import datetime
import os
import random

pygame.init()

# Constants
FPS = 120
MAX_PASSENGERS = 10000
BASE_SPAWN_RATE = 200
SPEED_MULTIPLIERS = [0, 0.05, 1.0, 5.0, 25.0, 50.0, 100.0]
PIN_TEXT_COLOR = (255, 255, 255)

# GA Config
GA_CONFIG = {
    'population_size': 10,
    'generations': 10,
    'elitism': 2,
    'mutation_rate': 0.3,
    'target_completed': 5000
}

# Initialize core objects
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Jeepney Simulation")

# Fonts
futuralt = pygame.font.Font('FUTURALT.TTF', 24)
small_font = pygame.font.Font('FUTURALT.TTF', 18)

class SimulationState:
    def __init__(self):
        self.speed_index = 2
        self.active_passengers = []
        self.waiting_passengers = {}
        self.grid_cache = {}
        self.metrics = {
            'total_commute': 0.0,
            'total_wait': 0.0,
            'total_fitness': 0.0,
            'completed': 0,
            'total_spawned': 0,
            'max_waiting': 0,
        }
        self.spawn_remainder = 0.0
        self.current_speed = SPEED_MULTIPLIERS[self.speed_index]
        self.target_speed = SPEED_MULTIPLIERS[self.speed_index]
        # Tracking actual simulation time separately from real time
        self.simulation_time = 0.0

    def reset_metrics(self):
        self.active_passengers = []
        self.waiting_passengers = {}
        self.spawn_remainder = 0.0
        self.simulation_time = 0.0
        self.metrics = {k: 0.0 if k != 'max_waiting' else 0 for k in self.metrics}

sim_state = SimulationState()

# Initialize routes and travel graph
jeep_set = JeepSet()
routes = jeep_set.routes
travel_graph = TravelGraph()
jeep_set.add_to_graph(travel_graph)
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
        sim_state.speed_index = min(len(SPEED_MULTIPLIERS)-1, sim_state.speed_index+1)
    elif key == pygame.K_LEFT:
        sim_state.speed_index = max(0, sim_state.speed_index-1)
    sim_state.target_speed = SPEED_MULTIPLIERS[sim_state.speed_index]

def spawn_passengers(dt):
    spawn_rate = BASE_SPAWN_RATE / 60 * dt
    spawn_count = int(spawn_rate + sim_state.spawn_remainder)
    sim_state.spawn_remainder = spawn_rate + sim_state.spawn_remainder - spawn_count

    for _ in range(spawn_count):
        if len(sim_state.active_passengers) >= MAX_PASSENGERS:
            break
        
        orig, dest = area_manager.get_random_origin_destination_pair()
        if not orig or not dest:
            continue
            
        p = Passenger()
        p.set_trip_between_areas(orig, dest)
        p.plan_route(travel_graph)
        
        if p.route:
            start = p.route[0]
            if start not in sim_state.grid_cache:
                sim_state.grid_cache[start] = get_grid_coors(*start)
            p.position = sim_state.grid_cache[start]
            # Initialize simulation_time attribute for tracking total time in system
            p.simulation_time = 0
            sim_state.active_passengers.append(p)
            sim_state.metrics['total_spawned'] += 1

def handle_completed_passengers():
    completed = [p for p in sim_state.active_passengers if p.state == "arrived"]
    sim_state.active_passengers = [p for p in sim_state.active_passengers if p not in completed]
    
    for p in completed:
        sim_state.metrics['total_commute'] += p.simulation_time
        sim_state.metrics['total_fitness'] += 100 * math.exp(-p.journey_time/60)
    sim_state.metrics['completed'] += len(completed)
    return completed

def update_waiting_passengers(dt):
    waiting = {}
    total_waiting = 0
    
    for p in sim_state.active_passengers:
        if p.state == "waiting_jeep":
            current_node = p.route[p.current_step]
            grid_pos = current_node[0] if isinstance(current_node, tuple) and len(current_node) == 3 else current_node
            jeep_id = current_node[2] if isinstance(current_node, tuple) and len(current_node) == 3 else -1

            if grid_pos not in waiting:
                waiting[grid_pos] = {}
            waiting[grid_pos][jeep_id] = waiting[grid_pos].get(jeep_id, 0) + 1
            total_waiting += 1

    sim_state.waiting_passengers = waiting
    sim_state.metrics['total_wait'] += total_waiting * dt  # Uses simulation time delta
    sim_state.metrics['max_waiting'] = max(sim_state.metrics['max_waiting'], total_waiting)

def update_passengers(dt):
    handle_completed_passengers()
    
    for p in sim_state.active_passengers:
        # Update simulation time for each passenger
        p.simulation_time += dt
        p.update_position(travel_graph, dt, routes)
        # Only increment journey time when moving (not waiting)
        if p.state not in ["waiting_jeep"]:
            p.journey_time += dt
        
    update_waiting_passengers(dt)
    
def draw_waiting_pins(screen, font):
    PIN_SPACING = 15
    for pos, jeep_counts in sim_state.waiting_passengers.items():
        if pos not in sim_state.grid_cache:
            sim_state.grid_cache[pos] = get_grid_coors(*pos)
        screen_pos = sim_state.grid_cache[pos]
        
        total_pins = len(jeep_counts)
        if total_pins == 0:
            continue
            
        start_offset = -((total_pins - 1) * PIN_SPACING) / 2
        for i, (jeep_id, count) in enumerate(jeep_counts.items()):
            if count <= 0:
                continue
                
            offset_x = start_offset + (i * PIN_SPACING)
            pin_color = routes[jeep_id].color if 0 <= jeep_id < len(routes) else (163, 163, 163)
            pin_pos = (screen_pos[0] + offset_x, screen_pos[1])
            draw_waiting_pin(screen, pin_pos, count, font, pin_color)

def draw_interface():
    finished_sum = sim_state.metrics['total_commute']
    active_sum = sum(p.simulation_time for p in sim_state.active_passengers)
    total_count = sim_state.metrics['completed'] + len(sim_state.active_passengers)
    avg_commute = (finished_sum + active_sum) / total_count if total_count > 0 else 0.0
    
    # Calculate current fitness with penalty (matching GAManager.log_fitness calculation)
    if sim_state.metrics['completed'] > 0:
        base_fit = sim_state.metrics['total_fitness'] / sim_state.metrics['completed']
        penalty = 0.1 * sim_state.metrics['max_waiting']  # Same penalty as in log_fitness
        current_fitness = max(0, base_fit - penalty)
    else:
        current_fitness = 0.0
    
    stats = [
        f"Average Commute: {format_time(avg_commute)}",
        f"Completed:       {sim_state.metrics['completed']}",
        f"Active:          {len(sim_state.active_passengers)}",
        f"Waiting:         {sum(sum(cnts.values()) for cnts in sim_state.waiting_passengers.values())}",
        f"Current Fitness: {current_fitness:.1f}",  # Changed to show penalized fitness
        f"Simulation Time: {format_time(sim_state.simulation_time)}",
    ]

    y = 20
    for text in stats:
        surf = futuralt.render(text, True, (0,0,0))
        screen.blit(surf, (20, y))
        y += 30

    speed_text = f"{sim_state.current_speed:.2f}× Speed"
    surf = small_font.render(speed_text, True, (0,0,0))
    screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, 20))

class GAManager:
    def __init__(self):
        self.population = [JeepSet() for _ in range(GA_CONFIG['population_size'])]
        self.current_gen = 0
        self.current_indiv = 0
        self.best_fitness = float('-inf')
        self.current_fitness = 0
        self.best_gen = 0
        self.best_indiv = 0
        self.filename = f"ga_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.init_log_file()

    def init_log_file(self):
        with open(self.filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'generation', 'individual', 'fitness', 'avg_commute', 'completed'])

    def log_fitness(self):
        completed = sim_state.metrics['completed']
        if completed == 0:
            self.current_fitness = 0
            return

        base_fit = sim_state.metrics['total_fitness'] / completed
        penalty = 0.1 * sim_state.metrics['max_waiting']
        self.current_fitness = max(0, base_fit - penalty)

        if self.current_fitness > self.best_fitness:
            self.best_fitness = self.current_fitness
            self.best_gen = self.current_gen
            self.best_indiv = self.current_indiv

        with open(self.filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                self.current_gen,
                self.current_indiv,
                self.current_fitness,
                sim_state.metrics['total_commute'] / completed,
                completed
            ])

    def advance_generation(self):
        sorted_pop = sorted(self.population, key=lambda ind: self.get_fitness(ind), reverse=True)
        new_pop = sorted_pop[:GA_CONFIG['elitism']]

        while len(new_pop) < GA_CONFIG['population_size']:
            parent1 = self.tournament_select()
            parent2 = self.tournament_select()
            child1, child2 = JeepSet.crossover(parent1, parent2)
            
            if random.random() < GA_CONFIG['mutation_rate']:
                child1.mutate()
            if random.random() < GA_CONFIG['mutation_rate']:
                child2.mutate()
            
            new_pop.extend([child1, child2])

        self.population = new_pop[:GA_CONFIG['population_size']]
        self.current_gen += 1
        self.current_indiv = 0

    def tournament_select(self, k=3):
        return max(random.sample(self.population, k), key=lambda ind: self.get_fitness(ind))

    def get_fitness(self, individual):
        return self.current_fitness if individual is self.population[self.current_indiv] else 0
    
def main_loop():
    ga = GAManager()
    last_time = pygame.time.get_ticks()
    
    # Initialize jeep_set with first individual from population
    global jeep_set, routes, travel_graph
    jeep_set = ga.population[0]
    routes = jeep_set.routes
    travel_graph = TravelGraph()
    jeep_set.add_to_graph(travel_graph)
    travel_graph.add_transfer_connections()

    while True:
        now = pygame.time.get_ticks()
        raw_dt = (now - last_time) / 1000.0
        last_time = now

        # Update simulation speed
        alpha = min(1.0, raw_dt / 0.1)
        sim_state.current_speed += (sim_state.target_speed - sim_state.current_speed) * alpha
        dt = raw_dt * sim_state.current_speed
        
        # Track simulation time
        sim_state.simulation_time += dt

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                handle_speed_change(event.key)

        # Simulation update
        if sim_state.metrics['completed'] < GA_CONFIG['target_completed']:
            spawn_passengers(dt)
            # Use the same dt for both movement and time tracking
            update_passengers(dt)
            
            # Update jeeps using the same dt
            for r in jeep_set:
                r.update(dt)
        else:
            ga.log_fitness()
            if ga.current_indiv + 1 < GA_CONFIG['population_size']:
                ga.current_indiv += 1
                # Update jeep_set to next individual
                jeep_set = ga.population[ga.current_indiv]
                routes = jeep_set.routes
                travel_graph = TravelGraph()
                jeep_set.add_to_graph(travel_graph)
                travel_graph.add_transfer_connections()
            else:
                if ga.current_gen < GA_CONFIG['generations'] - 1:
                    ga.advance_generation()
                    # Update jeep_set to first individual of new generation
                    jeep_set = ga.population[0]
                    routes = jeep_set.routes
                    travel_graph = TravelGraph()
                    jeep_set.add_to_graph(travel_graph)
                    travel_graph.add_transfer_connections()
                else:
                    print("GA Complete!")
                    pygame.quit()
                    sys.exit()

            # Reset simulation metrics
            sim_state.reset_metrics()

        # Rendering
        screen.fill((255, 255, 255))
        draw_grid(screen)
        area_manager.draw(screen)

        for r in jeep_set:
            r.drawRoute(screen)
            r.drawJeep(screen)

        for p in sim_state.active_passengers:
            p.draw(screen)

        draw_waiting_pins(screen, area_manager.font)
        draw_interface()

        # Draw GA status
        ga_status = [
            f"Generation: {ga.current_gen}/{GA_CONFIG['generations']-1}",
            f"Individual: {ga.current_indiv+1}/{GA_CONFIG['population_size']}",
            f"Best Fitness: {ga.best_fitness:.1f} (Gen {ga.best_gen} Ind {ga.best_indiv})"
        ]
        y = SCREEN_HEIGHT - 120
        for line in ga_status:
            text = futuralt.render(line, True, (0, 0, 0))
            screen.blit(text, (20, y))
            y += 30

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main_loop()