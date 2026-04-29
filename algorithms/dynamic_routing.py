import networkx as nx
from ml.traffic_model import predict_traffic

def dynamic_routing(G, source, target, time_of_day):
    """
    Modify edge weights based on predicted traffic and compute shortest path.
    """
    # Predict traffic for each edge (simplified, assume traffic affects all edges similarly)
    traffic_level = predict_traffic(time_of_day)
    # Modify weights: increase by traffic factor
    traffic_factor = 1 + traffic_level / 10  # Example: traffic_level 0-10, factor 1-2

    # Create a copy of the graph with modified weights
    G_modified = G.copy()
    for u, v, data in G_modified.edges(data=True):
        data['weight'] = data.get('length', 1) * traffic_factor

    try:
        path = nx.shortest_path(G_modified, source, target, weight='weight')
        length = nx.shortest_path_length(G_modified, source, target, weight='weight')
        return path, length
    except nx.NetworkXNoPath:
        return None, float('inf')