import osmnx as ox
import networkx as nx

# Define the place
place = "Navi Mumbai, India"

# Get the road network
G = ox.graph_from_place(place, network_type='drive')

# Save as GraphML
ox.save_graphml(G, filepath="navi_mumbai.graphml")

print("Graph saved as navi_mumbai.graphml")