import folium
from folium.plugins import HeatMap
import osmnx as ox

def create_base_map(G, center_lat, center_lon):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
    return m

def add_markers(m, locations, labels=None):
    for i, (lat, lon) in enumerate(locations):
        label = labels[i] if labels else f"Stop {i+1}"
        folium.Marker([lat, lon], popup=label).add_to(m)

def add_route(m, G, route_nodes):
    # Get coords
    coords = []
    for node in route_nodes:
        lat, lon = G.nodes[node]['y'], G.nodes[node]['x']
        coords.append([lat, lon])
    folium.PolyLine(coords, color='blue', weight=5).add_to(m)

def visualize_route(G, locations, route_nodes):
    if not locations:
        return folium.Map()
    center_lat, center_lon = locations[0]
    m = create_base_map(G, center_lat, center_lon)
    labels = [f"Stop {i+1}" for i in range(len(locations))]
    add_markers(m, locations, labels)
    add_route(m, G, route_nodes)
    return m