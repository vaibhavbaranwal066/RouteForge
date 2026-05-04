import networkx as nx
import osmnx as ox
from geopy.distance import geodesic
from algorithms.utils import calculate_travel_time

def greedy_vrp(G, locations, start_location=None, traffic_level=0):
    """
    Greedy Vehicle Routing Problem: start from first location, visit nearest unvisited.
    
    Args:
        G: NetworkX graph
        locations: list of (lat, lon) tuples
        start_location: starting location (default: first location)
        traffic_level: traffic level 0-10
    
    Returns:
        (route_nodes, total_distance_meters, total_time_seconds)
    """
    if not locations:
        return [], 0, 0

    # Find nearest nodes in graph
    nodes = []
    for loc in locations:
        nearest_node = ox.distance.nearest_nodes(G, loc[1], loc[0])  # lon, lat
        nodes.append(nearest_node)

    if start_location:
        start_node = ox.distance.nearest_nodes(G, start_location[1], start_location[0])
    else:
        start_node = nodes[0]

    unvisited = set(nodes)
    current = start_node
    route = [current]
    total_distance = 0

    while unvisited:
        # Find nearest unvisited
        nearest = min(unvisited, key=lambda n: nx.shortest_path_length(G, current, n, weight='length'))
        try:
            dist = nx.shortest_path_length(G, current, nearest, weight='length')
            total_distance += dist
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        except nx.NetworkXNoPath:
            break  # Skip if no path

    # Calculate time
    total_time = calculate_travel_time(total_distance, traffic_level=traffic_level)
    
    return route, total_distance, total_time