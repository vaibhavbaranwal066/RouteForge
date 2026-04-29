import osmnx as ox

def find_nearest_node(G, lat, lon):
    return ox.distance.nearest_nodes(G, lon, lat)

def get_node_coords(G, node):
    return G.nodes[node]['y'], G.nodes[node]['x']  # lat, lon