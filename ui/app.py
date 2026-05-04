import streamlit as st
import osmnx as ox
import networkx as nx
from streamlit_folium import st_folium
import folium
from algorithms.dijkstra import dijkstra_shortest_path
from algorithms.dynamic_routing import dynamic_routing
from algorithms.vrp_optimizer import greedy_vrp
from algorithms.astar import astar_shortest_path
from algorithms.utils import format_time
from visualization.map_visualizer import visualize_route
from visualization.traffic_heatmap import create_traffic_heatmap
from visualization.demand_heatmap import create_demand_heatmap
from visualization.algorithm_comparison import display_algorithm_comparison
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
st.set_page_config(page_title="Smart Delivery Route Optimization", layout="wide")
st.title("Smart Delivery Route Optimization System")

# Sidebar
st.sidebar.header("Controls")
algorithm = st.sidebar.selectbox(
    "Select Algorithm", 
    ["Dijkstra", "A* Algorithm", "Dynamic Routing", "VRP Optimization"]
)
time_of_day = st.sidebar.slider("Time of Day (hour)", 0, 23, 12)
compare_all = st.sidebar.checkbox("Compare All Algorithms", value=False)
compute_route = st.sidebar.button("Compute Route")

if st.sidebar.button("Clear Locations"):
    st.session_state.locations = []
    st.session_state.computed = False
    st.rerun()

# Session state for locations
if 'locations' not in st.session_state:
    st.session_state.locations = []

if 'computed' not in st.session_state:
    st.session_state.computed = False

if 'algorithm_results' not in st.session_state:
    st.session_state.algorithm_results = {}

# Map
st.header("Interactive Map - Click to Select Locations")
m = folium.Map(location=[19.0330, 73.0297], zoom_start=12)  # Navi Mumbai center

# Add existing markers with Source/Destination distinction
for i, (lat, lon) in enumerate(st.session_state.locations):
    if i == 0:
        folium.Marker(
            [lat, lon],
            popup=f"SOURCE (Stop {i+1})",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(m)
    elif i == len(st.session_state.locations) - 1:
        folium.Marker(
            [lat, lon],
            popup=f"DESTINATION (Stop {i+1})",
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(m)
    else:
        folium.Marker(
            [lat, lon],
            popup=f"Stop {i+1}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

# Get map click
map_data = st_folium(m, width=1400, height=600)

if map_data and map_data.get('last_clicked'):
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    st.session_state.locations.append((lat, lon))
    st.rerun()

# Display selected locations
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.write(f"**Selected Locations: {len(st.session_state.locations)}**")
    for i, loc in enumerate(st.session_state.locations):
        if i == 0:
            st.write(f"🟢 **SOURCE (Stop {i+1})**: {loc}")
        elif i == len(st.session_state.locations) - 1:
            st.write(f"🔴 **DESTINATION (Stop {i+1})**: {loc}")
        else:
            st.write(f"🔵 Stop {i+1}: {loc}")

with col2:
    if st.button("Remove Last Location"):
        if st.session_state.locations:
            st.session_state.locations.pop()
            st.rerun()

with col3:
    if st.button("Clear All"):
        st.session_state.locations = []
        st.session_state.computed = False
        st.rerun()

# Compute route(s)
if compute_route and len(st.session_state.locations) >= 2:
    st.session_state.computed = True
    locations = st.session_state.locations
    
    traffic_level = predict_traffic(time_of_day)
    
    if compare_all:
        # Compute all algorithms
        st.session_state.algorithm_results = {}
        
        try:
            # Dijkstra
            source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
            target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
            path, dist, time_seconds = dijkstra_shortest_path(G, source, target, traffic_level=traffic_level)
            if path:
                st.session_state.algorithm_results['Dijkstra'] = (dist, time_seconds)
        except Exception as e:
            st.warning(f"Dijkstra failed: {e}")
        
        try:
            # A* Algorithm
            source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
            target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
            path, dist, time_seconds = astar_shortest_path(G, source, target)
            if path:
                from algorithms.utils import calculate_travel_time
                time_seconds = calculate_travel_time(dist, traffic_level=traffic_level)
                st.session_state.algorithm_results['A* Algorithm'] = (dist, time_seconds)
        except Exception as e:
            st.warning(f"A* Algorithm failed: {e}")
        
        try:
            # Dynamic Routing
            source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
            target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
            path, dist, time_seconds = dynamic_routing(G, source, target, time_of_day)
            if path:
                st.session_state.algorithm_results['Dynamic Routing'] = (dist, time_seconds)
        except Exception as e:
            st.warning(f"Dynamic Routing failed: {e}")
        
        try:
            # VRP Optimization
            route_nodes, dist, time_seconds = greedy_vrp(G, locations, traffic_level=traffic_level)
            if route_nodes:
                st.session_state.algorithm_results['VRP Optimization'] = (dist, time_seconds)
        except Exception as e:
            st.warning(f"VRP Optimization failed: {e}")
    else:
        # Compute single algorithm
        if algorithm == "Dijkstra":
            source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
            target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
            path, dist, time_seconds = dijkstra_shortest_path(G, source, target, traffic_level=traffic_level)
            st.session_state.route_map = visualize_route(G, locations, path, show_source_dest=True)
            st.session_state.dist = dist
            st.session_state.time = time_seconds
            st.session_state.algorithm_name = "Dijkstra"
        
        elif algorithm == "A* Algorithm":
            source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
            target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
            path, dist, _ = astar_shortest_path(G, source, target)
            if path:
                from algorithms.utils import calculate_travel_time
                time_seconds = calculate_travel_time(dist, traffic_level=traffic_level)
                st.session_state.route_map = visualize_route(G, locations, path, show_source_dest=True)
                st.session_state.dist = dist
                st.session_state.time = time_seconds
                st.session_state.algorithm_name = "A* Algorithm"
            else:
                st.error("A* could not find a path!")
        
        elif algorithm == "Dynamic Routing":
            source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
            target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
            path, dist, time_seconds = dynamic_routing(G, source, target, time_of_day)
            st.session_state.route_map = visualize_route(G, locations, path, show_source_dest=True)
            st.session_state.dist = dist
            st.session_state.time = time_seconds
            st.session_state.algorithm_name = "Dynamic Routing"
        
        elif algorithm == "VRP Optimization":
            route_nodes, dist, time_seconds = greedy_vrp(G, locations, traffic_level=traffic_level)
            st.session_state.route_map = visualize_route(G, locations, route_nodes, show_source_dest=True)
            st.session_state.dist = dist
            st.session_state.time = time_seconds
            st.session_state.algorithm_name = "VRP Optimization"

# Display route if computed
if st.session_state.computed and len(st.session_state.locations) >= 2:
    if compare_all and st.session_state.algorithm_results:
        st.header("Algorithm Comparison Results")
        
        # Create tabs for individual algorithms and comparison
        tabs = st.tabs(["📊 Comparison", "📍 Details"])
        
        with tabs[0]:
            display_algorithm_comparison(st.session_state.algorithm_results)
        
        with tabs[1]:
            st.subheader("Individual Algorithm Results")
            for algo, (dist, time_sec) in st.session_state.algorithm_results.items():
                with st.expander(f"{algo}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Distance", f"{dist/1000:.2f} km", f"{dist:.0f} m")
                    with col2:
                        st.metric("Time", format_time(time_sec), f"{time_sec:.0f} s")
                    with col3:
                        speed = (dist / time_sec * 3.6) if time_sec > 0 else 0
                        st.metric("Speed", f"{speed:.2f} km/h")
    else:
        if 'route_map' in st.session_state:
            st.header(f"Optimized Route - {st.session_state.algorithm_name}")
            st_folium(st.session_state.route_map, width=1400, height=600)
            
            # Display metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Distance", f"{st.session_state.dist/1000:.2f} km", f"{st.session_state.dist:.0f} m")
            with col2:
                st.metric("Time", format_time(st.session_state.time), f"{st.session_state.time:.0f} s")
            with col3:
                speed = (st.session_state.dist / st.session_state.time * 3.6) if st.session_state.time > 0 else 0
                st.metric("Speed", f"{speed:.2f} km/h")
            with col4:
                st.metric("Algorithm", st.session_state.algorithm_name)

# Analytics
st.header("Analytics Dashboard")
traffic = predict_traffic(time_of_day)
demand = predict_demand(1)  # Next day

col1, col2 = st.columns(2)
with col1:
    st.metric("Predicted Traffic Level", f"{traffic:.2f}/10", "Current time of day")
with col2:
    st.metric("Predicted Demand", f"{demand:.2f}", "Next day forecast")

# Heatmaps
st.header("Heatmap Visualizations")
col1, col2 = st.columns(2)

with col1:
    if st.button("Show Traffic Heatmap"):
        st.session_state.show_traffic_hm = True

with col2:
    if st.button("Show Demand Heatmap"):
        st.session_state.show_demand_hm = True

if st.session_state.get('show_traffic_hm'):
    st.subheader("Traffic Heatmap")
    hm = create_traffic_heatmap(G, time_of_day)
    st_folium(hm, width=1400, height=600)

if st.session_state.get('show_demand_hm'):
    st.subheader("Demand Heatmap")
    hm = create_demand_heatmap(G, 1)
    st_folium(hm, width=1400, height=600)