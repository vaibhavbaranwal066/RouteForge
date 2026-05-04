import networkx as nx
import heapq
from algorithms.utils import calculate_travel_time

def dijkstra_shortest_path(G, source, target, traffic_level=0):
    """
    Compute the shortest path using Dijkstra's algorithm.
    Returns: (path, distance_meters, time_seconds)
    """
    try:
        path = nx.dijkstra_path(G, source, target, weight='length')
        distance = nx.dijkstra_path_length(G, source, target, weight='length')
        time_seconds = calculate_travel_time(distance, traffic_level=traffic_level)
        return path, distance, time_seconds
    except nx.NetworkXNoPath:
        return None, float('inf'), float('inf')

def dijkstra_all_paths(G, source):
    """
    Compute shortest paths from source to all nodes.
    """
    return nx.single_source_dijkstra_path_length(G, source, weight='length')