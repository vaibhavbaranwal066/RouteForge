import folium
from folium.plugins import HeatMap
from ml.demand_forecast import predict_demand

def create_demand_heatmap(G, day):
    m = folium.Map()
    heat_data = []
    for node in G.nodes():
        lat, lon = G.nodes[node]['y'], G.nodes[node]['x']
        # Simplified: demand based on node
        demand = predict_demand(day) / 100  # Normalize
        heat_data.append([lat, lon, demand])
    HeatMap(heat_data).add_to(m)
    return m