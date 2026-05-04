import networkx as nx
from heapq import heappush, heappop
import math

def haversine_distance(node1_data, node2_data):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    lat1 = node1_data['y']
    lon1 = node1_data['x']
    lat2 = node2_data['y']
    lon2 = node2_data['x']
    
    # convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r

def astar_shortest_path(G, source, target):
    """
    Compute the shortest path using A* algorithm.
    Returns path, distance, and 0 (for compatibility with other algorithms).
    """
    try:
        # Get target node data for heuristic
        target_data = G.nodes[target]
        
        # Open set: priority queue of (f_score, counter, node)
        open_set = [(0, 0, source)]
        counter = 0
        
        # Track visited nodes
        came_from = {}
        g_score = {node: float('inf') for node in G.nodes()}
        g_score[source] = 0
        
        # Track f_score for all nodes
        f_score = {node: float('inf') for node in G.nodes()}
        h_source = haversine_distance(G.nodes[source], target_data)
        f_score[source] = h_source
        
        open_set_hash = {source}
        
        while open_set:
            current_f, _, current = heappop(open_set)
            
            if current == target:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                
                # Calculate distance
                distance = 0
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    # Find the edge with minimum length (in case of multi-edges)
                    if G.has_edge(u, v):
                        edge_data = G[u][v]
                        if isinstance(edge_data, dict):
                            distance += edge_data.get('length', 1)
                        else:
                            # Handle multi-edges
                            min_length = float('inf')
                            for key in edge_data:
                                min_length = min(min_length, edge_data[key].get('length', 1))
                            distance += min_length
                
                return path, distance, 0
            
            open_set_hash.discard(current)
            
            # Check all neighbors
            for neighbor in G.neighbors(current):
                # Get edge weight (length)
                edge_data = G[current][neighbor]
                if isinstance(edge_data, dict):
                    tentative_g = g_score[current] + edge_data.get('length', 1)
                else:
                    # Handle multi-edges by taking minimum
                    min_length = float('inf')
                    for key in edge_data:
                        min_length = min(min_length, edge_data[key].get('length', 1))
                    tentative_g = g_score[current] + min_length
                
                if tentative_g < g_score[neighbor]:
                    # This path is the best so far
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h_neighbor = haversine_distance(G.nodes[neighbor], target_data)
                    f_score[neighbor] = tentative_g + h_neighbor
                    
                    if neighbor not in open_set_hash:
                        counter += 1
                        heappush(open_set, (f_score[neighbor], counter, neighbor))
                        open_set_hash.add(neighbor)
        
        # No path found
        return None, float('inf'), 0
    except Exception as e:
        print(f"A* Error: {e}")
        return None, float('inf'), 0
