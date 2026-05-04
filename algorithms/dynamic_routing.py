import networkx as nx
from ml.traffic_model import predict_traffic
from algorithms.utils import calculate_travel_time

def dynamic_routing(G, source, target, time_of_day):
    """
    Modify edge weights based on predicted traffic and compute shortest path.
    Returns: (path, distance_meters, time_seconds)
    """
    # Predict traffic for each edge and apply variable traffic weights
    traffic_level = predict_traffic(time_of_day)
    base_traffic_factor = 1 + traffic_level / 10  # Example: traffic_level 0-10, factor 1-2

    # Create a copy of the graph with modified weights
    G_modified = G.copy()
    for u, v, data in G_modified.edges(data=True):
        length = data.get('length', 1)
        # Apply a deterministic per-edge congestion factor so routing can differ
        congestion_bias = ((u + v + time_of_day) % 5) * 0.1  # 0.0 to 0.4
        data['weight'] = length * (base_traffic_factor + congestion_bias)

    try:
        path = nx.shortest_path(G_modified, source, target, weight='weight')
        # Calculate actual distance of the path found (on original graph)
        actual_distance = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if G.has_edge(u, v):
                edge_data = G[u][v]
                if isinstance(edge_data, dict):
                    actual_distance += edge_data.get('length', 1)
                else:
                    # Handle multi-edges
                    min_length = float('inf')
                    for key in edge_data:
                        min_length = min(min_length, edge_data[key].get('length', 1))
                    actual_distance += min_length
        # Calculate time with traffic
        time_seconds = calculate_travel_time(actual_distance, traffic_level=traffic_level)
        return path, actual_distance, time_seconds
    except nx.NetworkXNoPath:
        return None, float('inf'), float('inf')