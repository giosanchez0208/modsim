import jeeproute
import time       
import heapq

# Constants for costs
WALKING_COST = 6
JEEPNEY_COST = 1
TRANSITION_PENALTY = 12
TRANSFER_PENALTY = 20 

class TravelGraph:
    def __init__(self):
        """walking costs 6 points"""
        self.graph = {}
        for x in range(17):
            for y in range(17):
                neighbors = []
                # Check left neighbor
                if x > 0:
                    neighbors.append(((x-1, y), WALKING_COST, "walk", None))
                # Check right neighbor
                if x < 16:
                    neighbors.append(((x+1, y), WALKING_COST, "walk", None))
                # Check down neighbor
                if y > 0:
                    neighbors.append(((x, y-1), WALKING_COST, "walk", None))
                # Check up neighbor
                if y < 16:
                    neighbors.append(((x, y+1), WALKING_COST, "walk", None))
                self.graph[(x, y)] = neighbors

    def addJeep(self, jeep_route, jeep_id):
        """riding a jeep costs 1 point, each jeep has a unique ID"""
        route_points = jeep_route.route_points
        if not route_points:
            return
        for i in range(len(route_points)):
            current = route_points[i]
            next_index = (i + 1) % len(route_points)
            next_point = route_points[next_index]
            if current in self.graph:
                self.graph[current].append((next_point, JEEPNEY_COST, "jeep", jeep_id))
            else:
                self.graph[current] = [(next_point, JEEPNEY_COST, "jeep", jeep_id)]

    def find_shortest_path(self, start, end):
        """
        The pathfinding algorithm will abide by the following costs:
        - Walking cost: 6 points per move
        - Jeepney cost: 1 point per move
        - Transition penalty: 12 points when switching from walking to jeepney
        - Transfer penalty: 8 points when switching between different jeep routes
        """

        heap = []
        # Format: (cost, node, transport_type, jeep_id, path)
        heapq.heappush(heap, (0, start, None, None, [start]))
        
        # Keep track of visited nodes with their cost, transport type, and jeep ID
        visited = {}
        
        while heap:
            current_cost, current_node, prev_transport, prev_jeep_id, path = heapq.heappop(heap)
            
            # Return path if destination reached
            if current_node == end:
                return (current_cost, path)
                
            # If we've already visited this node with a lower cost with the same transport mode and jeep ID, skip
            visit_key = (current_node, prev_transport, prev_jeep_id)
            if visit_key in visited and visited[visit_key] <= current_cost:
                continue
                
            visited[visit_key] = current_cost
            
            for neighbor, edge_weight, transport_type, jeep_id in self.graph.get(current_node, []):
                new_cost = current_cost + edge_weight
                
                # Transition Penalty
                if prev_transport == "walk" and transport_type == "jeep":
                    new_cost += TRANSITION_PENALTY
                
                # Transfer Penalty
                if prev_transport == "jeep" and transport_type == "jeep" and prev_jeep_id != jeep_id:
                    new_cost += TRANSFER_PENALTY
                
                # Only push to heap no better path
                new_visit_key = (neighbor, transport_type, jeep_id)
                if new_visit_key not in visited or new_cost < visited[new_visit_key]:
                    new_path = path + [neighbor]
                    heapq.heappush(heap, (new_cost, neighbor, transport_type, jeep_id, new_path))
                    
        # If no path found
        return (float('inf'), [])