import heapq
import random

WALKING_COST = 16
JEEPNEY_COST = 4
TRANSITION_PENALTY = 8
TRANSFER_PENALTY = 16

class TravelGraph:
    def __init__(self):
        self.graph = {}
        # Create basic walking grid
        for x in range(17):
            for y in range(17):
                node = (x, y)
                self.graph[node] = []
                # Add walking edges
                if x > 0:
                    self.graph[node].append(((x-1, y), WALKING_COST, "walk"))
                if x < 16:
                    self.graph[node].append(((x+1, y), WALKING_COST, "walk"))
                if y > 0:
                    self.graph[node].append(((x, y-1), WALKING_COST, "walk"))
                if y < 16:
                    self.graph[node].append(((x, y+1), WALKING_COST, "walk"))
    
    def _create_transition_node(self, point, jeep_id):
        # Create a transition node for boarding a jeepney
        return (point, 'transition', jeep_id)
    
    def _create_transfer_node(self, point, from_jeep_id, to_jeep_id):
        # Create a transfer node between jeepneys
        return (point, 'transfer', (from_jeep_id, to_jeep_id))
    
    def addJeep(self, jeep_route, jeep_id):
        points = jeep_route.route_points
        
        # First, add all transition nodes (from grid point to jeepney)
        for point in points:

            transition_node = self._create_transition_node(point, jeep_id)
            # Connect grid point to transition node (boarding)
            if point in self.graph:
                self.graph[point].append((transition_node, TRANSITION_PENALTY, "transition"))
            else:
                self.graph[point] = [(transition_node, TRANSITION_PENALTY, "transition")]
            
            # Create entry for transition node if it doesn't exist
            if transition_node not in self.graph:
                self.graph[transition_node] = []
        
        # Now add the jeepney route connections between transition nodes
        for i in range(len(points) - 1):
            current = points[i]
            next_point = points[i + 1]
            current_transition = self._create_transition_node(current, jeep_id)
            next_transition = self._create_transition_node(next_point, jeep_id)
            self.graph[current_transition].append((next_transition, JEEPNEY_COST, "jeep"))
            self.graph[current_transition].append((current, 0, "alight"))

        # Close the Loop
        if len(points) > 1:
            first_transition = self._create_transition_node(points[0], jeep_id)
            last_transition  = self._create_transition_node(points[-1], jeep_id)
            # riding from the last stop back to the first stop
            self.graph[last_transition].append((first_transition, JEEPNEY_COST, "jeep"))

        # Add option to alight at the last point
        last_point      = points[-1]
        last_transition = self._create_transition_node(last_point, jeep_id)
        self.graph[last_transition].append((last_point, 0, "alight"))
    
    def add_transfer_connections(self):
        # Add transfer nodes between different jeepney routes that share points
        point_to_jeeps = {}
        for node in self.graph:
            if isinstance(node, tuple) and len(node) == 3 and node[1] == 'transition':
                point, _, jeep_id = node
                if point not in point_to_jeeps:
                    point_to_jeeps[point] = []
                point_to_jeeps[point].append(jeep_id)
        
        # For each point with multiple jeepneys, create transfer nodes
        for point, jeep_ids in point_to_jeeps.items():
            if len(jeep_ids) > 1:
                # Create transfer connections between all pairs of jeepneys
                for from_jeep in jeep_ids:
                    for to_jeep in jeep_ids:
                        if from_jeep != to_jeep:
                            from_transition = self._create_transition_node(point, from_jeep)
                            to_transition = self._create_transition_node(point, to_jeep)
                            
                            # Create transfer node
                            transfer_node = self._create_transfer_node(point, from_jeep, to_jeep)
                            
                            # Add to graph if not exists
                            if transfer_node not in self.graph:
                                self.graph[transfer_node] = []
                            
                            # Connect from transition -> transfer -> to transition
                            self.graph[from_transition].append((transfer_node, TRANSFER_PENALTY, "transfer"))
                            self.graph[transfer_node].append((to_transition, 0, "complete_transfer"))
    
    def find_shortest_path(self, start, end):
        # Create a custom tuple for the heap that ensures proper comparison
        # The format is (cost, unique_id, node, path)
        # The unique_id ensures we don't try to compare nodes directly
        heap = [(0, 0, start, [start])]
        visited = {}
        unique_counter = 1
        
        while heap:
            cost, _, node, path = heapq.heappop(heap)
            
            if node == end:
                return (cost, path)
            
            if node in visited and visited[node] <= cost:
                continue
                    
            visited[node] = cost
            
            for neighbor, weight, edge_type in self.graph.get(node, []):
                new_cost = cost + weight
                if neighbor not in visited or new_cost < visited[neighbor]:
                    new_path = path + [neighbor]
                    # Use unique_counter to ensure proper comparison in heap
                    heapq.heappush(heap, (new_cost, unique_counter, neighbor, new_path))
                    unique_counter += 1
        
        return (float('inf'), [])
    
    def analyze_path(self, path, print_details=False):
        if not path or len(path) < 2:
            return {"total_cost": float('inf')}
        
        total_cost = 0
        jeep_segments = 0
        walking_segments = 0
        transfers = 0
        
        # Count different segments and transitions
        current_mode = None
        
        for i in range(len(path) - 1):
            curr = path[i]
            next_node = path[i + 1]
            
            # Find the edge between these nodes
            edge_cost = None
            edge_type = None
            
            for neighbor, cost, edge in self.graph.get(curr, []):
                if neighbor == next_node:
                    edge_cost = cost
                    edge_type = edge
                    break
            
            if edge_cost is not None:
                total_cost += edge_cost
                
                # Count segments
                if edge_type == "walk" and current_mode != "walk":
                    walking_segments += 1
                elif edge_type == "jeep" and current_mode != "jeep":
                    jeep_segments += 1
                elif edge_type == "transfer":
                    transfers += 1
                
                # Update current mode
                if edge_type in ["walk", "jeep"]:
                    current_mode = edge_type
        
        if print_details:
            print(f"Total cost: {total_cost}")
            print(f"Jeepney segments: {jeep_segments}")
            print(f"Walking segments: {walking_segments}")
            print(f"Transfers: {transfers}")
            
            # Print path details for debugging
            print("Path details:")
            for i in range(len(path) - 1):
                curr = path[i]
                next_node = path[i + 1]
                edge_info = "Unknown"
                
                for neighbor, cost, edge in self.graph.get(curr, []):
                    if neighbor == next_node:
                        edge_info = f"{edge} (cost: {cost})"
                        break
                
                print(f"  {curr} -> {next_node}: {edge_info}")
        
        return {
            "total_cost": total_cost,
            "jeep_segments": jeep_segments,
            "walking_segments": walking_segments,
            "transfers": transfers
        }

class Passenger:
    def __init__(self, origin=None, destination=None):
        self.origin = origin
        self.destination = destination
        self.route = []
        self.cost = float('inf')

    def plan_route(self, travel_graph):
        if not self.origin or not self.destination:
            return False
        self.cost, self.route = travel_graph.find_shortest_path(self.origin, self.destination)
        return bool(self.route)

    def get_route_analysis(self, travel_graph):
        return travel_graph.analyze_path(self.route, print_details=True)

    def set_random_trip(self, grid_size=17):
        while True:
            self.origin = (random.randint(0, grid_size - 1), random.randint(0, grid_size - 1))
            self.destination = (random.randint(0, grid_size - 1), random.randint(0, grid_size - 1))
            if self.origin != self.destination:
                break