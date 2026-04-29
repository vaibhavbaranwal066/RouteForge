import streamlit as st
import osmnx as ox
import networkx as nx
from streamlit_folium import st_folium
import folium
from algorithms.dijkstra import dijkstra_shortest_path
from algorithms.dynamic_routing import dynamic_routing
from algorithms.vrp_optimizer import greedy_vrp
from visualization.map_visualizer import visualize_route
from visualization.traffic_heatmap import create_traffic_heatmap
from visualization.demand_heatmap import create_demand_heatmap
from ml.traffic_model import predict_traffic
from ml.demand_forecast import predict_demand
import datetime

# Load graph
@st.cache_resource
def load_graph():
    try:
        G = ox.load_graphml("data/navi_mumbai.graphml")
    except:
        # Fallback to download
        G = ox.graph_from_place("Navi Mumbai, India", network_type='drive')
    return G

G = load_graph()

# App
st.title("Smart Delivery Route Optimization System")

# Sidebar
st.sidebar.header("Controls")
algorithm = st.sidebar.selectbox("Select Algorithm", ["Dijkstra", "Dynamic Routing", "VRP Optimization"])
time_of_day = st.sidebar.slider("Time of Day (hour)", 0, 23, 12)
compute_route = st.sidebar.button("Compute Route")

# Session state for locations
if 'locations' not in st.session_state:
    st.session_state.locations = []

if 'computed' not in st.session_state:
    st.session_state.computed = False

# Map
st.header("Interactive Map")
m = folium.Map(location=[19.0330, 73.0297], zoom_start=12)  # Navi Mumbai center

# Add existing markers
for i, (lat, lon) in enumerate(st.session_state.locations):
    folium.Marker([lat, lon], popup=f"Stop {i+1}").add_to(m)

# Get map click
map_data = st_folium(m, width=900, height=600)

if map_data['last_clicked']:
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    st.session_state.locations.append((lat, lon))
    # Removed st.rerun() to prevent clearing computed route

# Display locations
st.write(f"Selected Locations: {len(st.session_state.locations)}")
for i, loc in enumerate(st.session_state.locations):
    st.write(f"Stop {i+1}: {loc}")

# Compute route
if compute_route and len(st.session_state.locations) >= 2:
    st.session_state.computed = True
    locations = st.session_state.locations
    if algorithm == "Dijkstra":
        # For simplicity, from first to last
        source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
        target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
        path, dist = dijkstra_shortest_path(G, source, target)
        route_map = visualize_route(G, locations, path)
    elif algorithm == "Dynamic Routing":
        source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
        target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
        path, dist = dynamic_routing(G, source, target, time_of_day)
        route_map = visualize_route(G, locations, path)
    elif algorithm == "VRP Optimization":
        route_nodes, dist = greedy_vrp(G, locations)
        route_map = visualize_route(G, locations, route_nodes)

    st.session_state.route_map = route_map
    st.session_state.dist = dist

# Display route if computed
if st.session_state.computed and len(st.session_state.locations) >= 2:
    st.header("Optimized Route")
    st_folium(st.session_state.route_map, width=900, height=600)
    st.write(f"Total Distance: {st.session_state.dist:.2f} meters")

# Analytics
st.header("Analytics Dashboard")
traffic = predict_traffic(time_of_day)
demand = predict_demand(1)  # Next day
st.write(f"Predicted Traffic Level: {traffic:.2f}")
st.write(f"Predicted Demand: {demand:.2f}")

# Heatmaps
if st.button("Show Traffic Heatmap"):
    hm = create_traffic_heatmap(G, time_of_day)
    st_folium(hm, width=900, height=600)

if st.button("Show Demand Heatmap"):
    hm = create_demand_heatmap(G, 1)
    st_folium(hm, width=900, height=600)