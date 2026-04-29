import networkx as nx
import heapq

def dijkstra_shortest_path(G, source, target):
    """
    Compute the shortest path using Dijkstra's algorithm.
    """
    try:
        path = nx.dijkstra_path(G, source, target, weight='length')
        length = nx.dijkstra_path_length(G, source, target, weight='length')
        return path, length
    except nx.NetworkXNoPath:
        return None, float('inf')

def dijkstra_all_paths(G, source):
    """
    Compute shortest paths from source to all nodes.
    """
    return nx.single_source_dijkstra_path_length(G, source, weight='length')