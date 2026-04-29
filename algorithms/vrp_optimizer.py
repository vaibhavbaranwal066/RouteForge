import networkx as nx
import osmnx as ox
from geopy.distance import geodesic

def greedy_vrp(G, locations, start_location=None):
    """
    Greedy Vehicle Routing Problem: start from first location, visit nearest unvisited.
    locations: list of (lat, lon) tuples
    """
    if not locations:
        return [], 0

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

    # Convert back to locations? Or return nodes
    return route, total_distance