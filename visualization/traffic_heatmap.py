import folium
from folium.plugins import HeatMap
from ml.traffic_model import predict_traffic

def create_traffic_heatmap(G, time_of_day):
    m = folium.Map()
    heat_data = []
    for node in G.nodes():
        lat, lon = G.nodes[node]['y'], G.nodes[node]['x']
        # Simplified: traffic based on node
        traffic = predict_traffic(time_of_day) / 10  # Normalize
        heat_data.append([lat, lon, traffic])
    HeatMap(heat_data).add_to(m)
    return m