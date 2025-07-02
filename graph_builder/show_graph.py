import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from geopy.distance import geodesic

def visualize_graph():
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    stations_path = os.path.join(DATA_DIR, 'stations_lignes_coords.csv')

    stations = pd.read_csv(stations_path)

    G = nx.Graph()
    for _, row in stations.iterrows():
        G.add_node(row['station_key'],
                   name=row['station'],
                   ligne=row['ligne'],
                   latitude=row['latitude'],
                   longitude=row['longitude'])

    for ligne, group in stations.groupby("ligne"):
        group_sorted = group.sort_values("ordre")
        previous = None
        for _, row in group_sorted.iterrows():
            if previous is not None:
                coord1 = (previous['latitude'], previous['longitude'])
                coord2 = (row['latitude'], row['longitude'])
                if pd.notnull(coord1[0]) and pd.notnull(coord1[1]) and pd.notnull(coord2[0]) and pd.notnull(coord2[1]):
                    distance = geodesic(coord1, coord2).meters
                else:
                    distance = None
                # Ignore les boucles (auto-connectées)
                if previous['station_key'] != row['station_key']:
                    G.add_edge(previous['station_key'], row['station_key'], ligne=ligne, distance=distance)
            previous = row

    pos = {node: (data['longitude'], data['latitude']) for node, data in G.nodes(data=True)}

    lignes = list(set(nx.get_edge_attributes(G, 'ligne').values()))
    cmap = get_cmap('tab20')
    color_map = {ligne: cmap(i % 20) for i, ligne in enumerate(sorted(lignes))}

    plt.figure(figsize=(15, 15))

    for ligne in sorted(lignes):
        edges = [(u, v) for u, v, d in G.edges(data=True) if d['ligne'] == ligne]
        nx.draw_networkx_edges(G, pos,
                               edgelist=edges,
                               edge_color=[color_map[ligne]],
                               width=2,
                               alpha=0.6,
                               label=ligne)

    nx.draw_networkx_nodes(G, pos,
                           node_size=20,
                           node_color='red',
                           alpha=0.8)

    labels = {node: data['name'] for node, data in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, font_color='black')

    plt.title("Réseau métro/RER Île-de-France - Visualisation améliorée")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.legend(title="Lignes", loc='upper right', fontsize=8)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    visualize_graph()
