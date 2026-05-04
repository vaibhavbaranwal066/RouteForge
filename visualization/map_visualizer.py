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

def add_markers_with_source_dest(m, locations, labels=None):
    """
    Add markers with Source (first) and Destination (last) marked distinctly
    """
    for i, (lat, lon) in enumerate(locations):
        label = labels[i] if labels else f"Stop {i+1}"
        
        # First location is Source
        if i == 0:
            folium.Marker(
                [lat, lon],
                popup=f"SOURCE: {label}",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
        # Last location is Destination
        elif i == len(locations) - 1:
            folium.Marker(
                [lat, lon],
                popup=f"DESTINATION: {label}",
                icon=folium.Icon(color='red', icon='stop', prefix='fa')
            ).add_to(m)
        # Intermediate stops
        else:
            folium.Marker(
                [lat, lon],
                popup=f"Stop: {label}",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

def add_route(m, G, route_nodes):
    # Get coords
    coords = []
    for node in route_nodes:
        lat, lon = G.nodes[node]['y'], G.nodes[node]['x']
        coords.append([lat, lon])
    folium.PolyLine(coords, color='blue', weight=5).add_to(m)

def visualize_route(G, locations, route_nodes, show_source_dest=True):
    if not locations:
        return folium.Map()
    center_lat, center_lon = locations[0]
    m = create_base_map(G, center_lat, center_lon)
    labels = [f"Stop {i+1}" for i in range(len(locations))]
    
    if show_source_dest:
        add_markers_with_source_dest(m, locations, labels)
    else:
        add_markers(m, locations, labels)
    
    add_route(m, G, route_nodes)
    return m