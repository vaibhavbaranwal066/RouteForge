import osmnx as ox

def find_nearest_node(G, lat, lon):
    return ox.distance.nearest_nodes(G, lon, lat)

def get_node_coords(G, node):
    return G.nodes[node]['y'], G.nodes[node]['x']  # lat, lon

def calculate_travel_time(distance_meters, traffic_level=0, speed_kmh=30):
    """
    Calculate travel time in seconds.
    
    Args:
        distance_meters: Distance in meters
        traffic_level: Traffic level 0-10 (0 = no traffic, 10 = heavy traffic)
        speed_kmh: Base speed in km/h (default 30 for urban area)
    
    Returns:
        Travel time in seconds
    """
    # Reduce speed based on traffic: each level reduces speed by 2 km/h
    adjusted_speed = max(speed_kmh - (traffic_level * 2), 5)  # Minimum 5 km/h
    
    # Convert speed from km/h to m/s
    speed_ms = adjusted_speed * 1000 / 3600
    
    # Calculate time in seconds
    time_seconds = distance_meters / speed_ms if speed_ms > 0 else float('inf')
    
    return time_seconds

def format_time(seconds):
    """
    Format time in seconds to human-readable format (HH:MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"