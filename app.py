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
import hashlib
import json

# App configuration MUST be first
st.set_page_config(page_title="Smart Delivery Route Optimization", layout="wide")

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

# Create a hash key for locations to detect changes
def get_locations_hash(locations):
    """Create a hash of locations for change detection"""
    return hashlib.md5(json.dumps(locations).encode()).hexdigest()

# App
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
    st.session_state.locations_hash = ""
    st.rerun()

# Session state initialization
if 'locations' not in st.session_state:
    st.session_state.locations = []

if 'computed' not in st.session_state:
    st.session_state.computed = False

if 'algorithm_results' not in st.session_state:
    st.session_state.algorithm_results = {}

if 'route_data' not in st.session_state:
    st.session_state.route_data = {}

if 'locations_hash' not in st.session_state:
    st.session_state.locations_hash = ""

if 'show_traffic_hm' not in st.session_state:
    st.session_state.show_traffic_hm = False

if 'show_demand_hm' not in st.session_state:
    st.session_state.show_demand_hm = False

if 'current_algorithm' not in st.session_state:
    st.session_state.current_algorithm = ""

if 'comparison_algorithms' not in st.session_state:
    st.session_state.comparison_algorithms = []

if 'last_compare_all' not in st.session_state:
    st.session_state.last_compare_all = False

# Cache map visualization with hash key
@st.cache_data(ttl=3600)
def get_route_visualization(locations_tuple, route_nodes_tuple, algo_name):
    """Cache route visualization based on locations and route"""
    route_map = visualize_route(G, list(locations_tuple), list(route_nodes_tuple), show_source_dest=True)
    return route_map

@st.cache_data(ttl=3600)
def get_location_selection_map(locations_tuple):
    """Cache location selection map"""
    m = folium.Map(location=[19.0330, 73.0297], zoom_start=12)
    
    for i, (lat, lon) in enumerate(list(locations_tuple)):
        if i == 0:
            folium.Marker(
                [lat, lon],
                popup=f"SOURCE (Stop {i+1})",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
        elif i == len(list(locations_tuple)) - 1:
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
    
    return m

# Helper function to compute path visiting all locations
def compute_multi_stop_path(algo_func, locations, graph, traffic_level, time_of_day):
    """
    Compute a path visiting all locations in sequence using the given algorithm.
    Returns: (full_route, total_distance, total_time)
    """
    full_route = []
    total_distance = 0
    total_time = 0
    
    # Convert locations to nearest graph nodes
    location_nodes = []
    for loc in locations:
        node = ox.distance.nearest_nodes(graph, loc[1], loc[0])
        location_nodes.append(node)
    
    # Compute path visiting each location in sequence
    for i in range(len(location_nodes) - 1):
        source = location_nodes[i]
        target = location_nodes[i + 1]
        
        try:
            if algo_func.__name__ == 'dijkstra_shortest_path':
                path, dist, time_sec = algo_func(graph, source, target, traffic_level=traffic_level)
            elif algo_func.__name__ == 'astar_shortest_path':
                path, dist, _ = algo_func(graph, source, target)
                from algorithms.utils import calculate_travel_time
                time_sec = calculate_travel_time(dist, traffic_level=traffic_level)
            elif algo_func.__name__ == 'dynamic_routing':
                path, dist, time_sec = algo_func(graph, source, target, time_of_day)
            else:
                path, dist, time_sec = None, 0, 0
            
            if path:
                # Add path (avoiding duplicate intermediate nodes)
                if not full_route:
                    full_route.extend(path)
                else:
                    full_route.extend(path[1:])  # Skip first node (already in route)
                total_distance += dist
                total_time += time_sec
            else:
                return None, float('inf'), float('inf')
        except Exception as e:
            return None, float('inf'), float('inf')
    
    return full_route, total_distance, total_time

# Location selection section
st.header("Interactive Map - Click to Select Locations")

# Create location selection map
location_map = folium.Map(location=[19.0330, 73.0297], zoom_start=12)

for i, (lat, lon) in enumerate(st.session_state.locations):
    if i == 0:
        folium.Marker(
            [lat, lon],
            popup=f"SOURCE (Stop {i+1})",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(location_map)
    elif i == len(st.session_state.locations) - 1:
        folium.Marker(
            [lat, lon],
            popup=f"DESTINATION (Stop {i+1})",
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(location_map)
    else:
        folium.Marker(
            [lat, lon],
            popup=f"Stop {i+1}",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(location_map)

# Get map click with unique key
map_data = st_folium(location_map, width=1400, height=600, key="location_map")

if map_data and map_data.get('last_clicked'):
    lat = map_data['last_clicked']['lat']
    lon = map_data['last_clicked']['lng']
    st.session_state.locations.append((lat, lon))
    st.session_state.locations_hash = ""  # Reset to trigger recomputation if needed
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
            st.session_state.locations_hash = ""
            st.rerun()

with col3:
    if st.button("Clear All"):
        st.session_state.locations = []
        st.session_state.computed = False
        st.session_state.locations_hash = ""
        st.rerun()

# Compute route(s) - only when button clicked
if compute_route and len(st.session_state.locations) >= 2:
    locations_hash = get_locations_hash(st.session_state.locations)
    
    # Recompute when locations or comparison mode changes
    recompute = (
        locations_hash != st.session_state.locations_hash or
        compare_all != st.session_state.last_compare_all
    )
    if recompute:
        st.session_state.locations_hash = locations_hash
        st.session_state.last_compare_all = compare_all
        st.session_state.computed = True
        locations = st.session_state.locations
    else:
        locations = st.session_state.locations
    with st.spinner("Computing route..."):
        traffic_level = predict_traffic(time_of_day)
        
        if compare_all:
            # Compute all algorithms
            st.session_state.algorithm_results = {}
            st.session_state.route_data = {}
            st.session_state.comparison_algorithms = []
            
            # Determine if we have multiple stops
            has_multiple_stops = len(locations) > 2
            
            try:
                # Dijkstra - visit all locations
                if has_multiple_stops:
                    path, dist, time_seconds = compute_multi_stop_path(dijkstra_shortest_path, locations, G, traffic_level, time_of_day)
                else:
                    source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
                    target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
                    path, dist, time_seconds = dijkstra_shortest_path(G, source, target, traffic_level=traffic_level)
                
                if path:
                    st.session_state.algorithm_results['Dijkstra'] = (dist, time_seconds)
                    st.session_state.route_data['Dijkstra'] = path
                    st.session_state.comparison_algorithms.append('Dijkstra')
            except Exception as e:
                st.error(f"Dijkstra failed: {e}")
            
            try:
                # A* Algorithm - visit all locations
                if has_multiple_stops:
                    path, dist, time_seconds = compute_multi_stop_path(astar_shortest_path, locations, G, traffic_level, time_of_day)
                else:
                    source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
                    target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
                    path, dist, _ = astar_shortest_path(G, source, target)
                    if path:
                        from algorithms.utils import calculate_travel_time
                        time_seconds = calculate_travel_time(dist, traffic_level=traffic_level)
                    else:
                        path, dist, time_seconds = None, float('inf'), float('inf')
                
                if path:
                    st.session_state.algorithm_results['A* Algorithm'] = (dist, time_seconds)
                    st.session_state.route_data['A* Algorithm'] = path
                    st.session_state.comparison_algorithms.append('A* Algorithm')
            except Exception as e:
                st.error(f"A* Algorithm failed: {e}")
            
            try:
                # Dynamic Routing - visit all locations
                if has_multiple_stops:
                    path, dist, time_seconds = compute_multi_stop_path(dynamic_routing, locations, G, traffic_level, time_of_day)
                else:
                    source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
                    target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
                    path, dist, time_seconds = dynamic_routing(G, source, target, time_of_day)
                
                if path:
                    st.session_state.algorithm_results['Dynamic Routing'] = (dist, time_seconds)
                    st.session_state.route_data['Dynamic Routing'] = path
                    st.session_state.comparison_algorithms.append('Dynamic Routing')
            except Exception as e:
                st.error(f"Dynamic Routing failed: {e}")
            
            try:
                # VRP Optimization
                route_nodes, dist, time_seconds = greedy_vrp(G, locations, traffic_level=traffic_level)
                if route_nodes:
                    st.session_state.algorithm_results['VRP Optimization'] = (dist, time_seconds)
                    st.session_state.route_data['VRP Optimization'] = route_nodes
                    st.session_state.comparison_algorithms.append('VRP Optimization')
            except Exception as e:
                st.error(f"VRP Optimization failed: {e}")
            
            st.success("✅ All algorithms computed successfully!")
        else:
            # Compute single algorithm
            route_path = None
            dist = 0
            time_seconds = 0
            
            if algorithm == "Dijkstra":
                source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
                target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
                path, dist, time_seconds = dijkstra_shortest_path(G, source, target, traffic_level=traffic_level)
                route_path = path
            
            elif algorithm == "A* Algorithm":
                source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
                target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
                path, dist, _ = astar_shortest_path(G, source, target)
                if path:
                    from algorithms.utils import calculate_travel_time
                    time_seconds = calculate_travel_time(dist, traffic_level=traffic_level)
                    route_path = path
                else:
                    st.error("A* could not find a path!")
            
            elif algorithm == "Dynamic Routing":
                source = ox.distance.nearest_nodes(G, locations[0][1], locations[0][0])
                target = ox.distance.nearest_nodes(G, locations[-1][1], locations[-1][0])
                path, dist, time_seconds = dynamic_routing(G, source, target, time_of_day)
                route_path = path
            
            elif algorithm == "VRP Optimization":
                route_path, dist, time_seconds = greedy_vrp(G, locations, traffic_level=traffic_level)
            
            if route_path:
                st.session_state.route_data['current'] = route_path
                st.session_state.algorithm_results['current'] = (dist, time_seconds)
                st.session_state.current_algorithm = algorithm
                st.success(f"✅ {algorithm} route computed successfully!")

# Display route if computed
if st.session_state.computed and len(st.session_state.locations) >= 2:
    st.divider()
    
    if compare_all and st.session_state.algorithm_results:
        st.header("🔄 Algorithm Comparison Results")
        
        # Create tabs for individual algorithms and comparison
        tabs = st.tabs(["📊 Comparison", "📍 Individual Routes", "📋 Details"])
        
        with tabs[0]:
            # Filter algorithm_results to only include comparison algorithms
            comparison_results = {algo: st.session_state.algorithm_results[algo] 
                                 for algo in st.session_state.comparison_algorithms 
                                 if algo in st.session_state.algorithm_results}
            if comparison_results:
                display_algorithm_comparison(comparison_results)
        
        with tabs[1]:
            st.subheader("Select Algorithm to View Route")
            # Only show comparison algorithms, not 'current'
            available_algos = [algo for algo in st.session_state.comparison_algorithms 
                              if algo in st.session_state.route_data]
            if available_algos:
                selected_algo = st.selectbox("Choose algorithm", available_algos)
            else:
                st.warning("No routes available")
                selected_algo = None
            
            if selected_algo and selected_algo in st.session_state.route_data:
                route_nodes = st.session_state.route_data[selected_algo]
                route_map = get_route_visualization(
                    tuple(st.session_state.locations),
                    tuple(route_nodes),
                    selected_algo
                )
                st_folium(route_map, width=1400, height=600, key=f"route_map_{selected_algo}")
                
                dist, time_sec = st.session_state.algorithm_results[selected_algo]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Distance", f"{dist/1000:.2f} km", f"{dist:.0f} m")
                with col2:
                    st.metric("Time", format_time(time_sec), f"{time_sec:.0f} s")
                with col3:
                    speed = (dist / time_sec * 3.6) if time_sec > 0 else 0
                    st.metric("Speed", f"{speed:.2f} km/h")
        
        with tabs[2]:
            st.subheader("Individual Algorithm Results")
            for algo in st.session_state.comparison_algorithms:
                if algo in st.session_state.algorithm_results:
                    dist, time_sec = st.session_state.algorithm_results[algo]
                    with st.expander(f"📍 {algo}", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Distance", f"{dist/1000:.2f} km", f"{dist:.0f} m")
                        with col2:
                            st.metric("Time", format_time(time_sec), f"{time_sec:.0f} s")
                        with col3:
                            speed = (dist / time_sec * 3.6) if time_sec > 0 else 0
                            st.metric("Speed", f"{speed:.2f} km/h")
    else:
        if st.session_state.route_data.get('current') and st.session_state.current_algorithm:
            if 'current' in st.session_state.algorithm_results:
                dist, time_sec = st.session_state.algorithm_results['current']
                algo_name = st.session_state.current_algorithm
                route_nodes = st.session_state.route_data['current']
            else:
                st.warning("Route data not available")
                algo_name = None
                route_nodes = None
            
            if algo_name and route_nodes:
                st.header(f"🗺️ Optimized Route - {algo_name}")
                
                # Display route map
                route_map = get_route_visualization(
                    tuple(st.session_state.locations),
                    tuple(route_nodes),
                    algo_name
                )
                st_folium(route_map, width=1400, height=600, key="optimized_route_map")
                
                # Display metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Distance", f"{dist/1000:.2f} km", f"{dist:.0f} m")
                with col2:
                    st.metric("Time", format_time(time_sec), f"{time_sec:.0f} s")
                with col3:
                    speed = (dist / time_sec * 3.6) if time_sec > 0 else 0
                    st.metric("Speed", f"{speed:.2f} km/h")
                with col4:
                    st.metric("Algorithm", algo_name)

st.divider()

# Analytics
st.header("📊 Analytics Dashboard")
traffic = predict_traffic(time_of_day)
demand = predict_demand(1)  # Next day

col1, col2 = st.columns(2)
with col1:
    st.metric("Predicted Traffic Level", f"{traffic:.2f}/10", "Current time of day")
with col2:
    st.metric("Predicted Demand", f"{demand:.2f}", "Next day forecast")

# Heatmaps
st.header("🌡️ Heatmap Visualizations")
col1, col2 = st.columns(2)

with col1:
    if st.button("Show Traffic Heatmap"):
        st.session_state.show_traffic_hm = not st.session_state.show_traffic_hm

with col2:
    if st.button("Show Demand Heatmap"):
        st.session_state.show_demand_hm = not st.session_state.show_demand_hm

if st.session_state.show_traffic_hm:
    st.subheader("Traffic Heatmap")
    hm = create_traffic_heatmap(G, time_of_day)
    st_folium(hm, width=1400, height=600, key="traffic_heatmap")

if st.session_state.show_demand_hm:
    st.subheader("Demand Heatmap")
    hm = create_demand_heatmap(G, 1)
    st_folium(hm, width=1400, height=600, key="demand_heatmap")