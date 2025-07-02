import sys
import os
import pandas as pd
import networkx as nx
import pickle
from geopy.distance import geodesic
import matplotlib.pyplot as plt

# -- Répertoires --
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def build_nodes():
    gares_path = os.path.join(DATA_DIR, "emplacement_des_gares_idf_aligned.csv")
    gares = pd.read_csv(gares_path)
    gares["latitude"] = gares["Geo Point"]
    gares["longitude"] = gares["Geo Shape"]
    nodes = gares[["gare_key", "nom_so_gar", "latitude", "longitude"]].drop_duplicates()
    nodes.to_csv(os.path.join(DATA_DIR, "graph_nodes.csv"), index=False)
    print(f"{len(nodes)} nœuds exportés dans graph_nodes.csv")

def join_coords_to_stations():
    stations_path = os.path.join(DATA_DIR, "Stations_IDF_aligned.csv")
    nodes_path = os.path.join(DATA_DIR, "graph_nodes.csv")

    stations = pd.read_csv(stations_path)
    nodes = pd.read_csv(nodes_path)

    stations["station_key"] = stations["station_key"].astype(str)
    nodes["gare_key"] = nodes["gare_key"].astype(str)

    stations = stations.merge(
        nodes[["gare_key", "latitude", "longitude"]],
        left_on="station_key",
        right_on="gare_key",
        how="left"
    )
    stations.drop(columns=["gare_key"], inplace=True)

    stations.to_csv(os.path.join(DATA_DIR, "stations_lignes_coords.csv"), index=False)
    return stations

def build_graph():
    stations = join_coords_to_stations()

    G = nx.Graph()

    # -- Création des noeuds --
    for _, row in stations.iterrows():
        node_id = row['station_key'] + "_" + str(row['ligne'])
        G.add_node(
            node_id,
            station_key=row['station_key'],
            name=row['station'],
            ligne=row['ligne'],
            latitude=row['latitude'],
            longitude=row['longitude']
        )

    # -- Ajout des arêtes "adjacence" sur la même ligne --
    for ligne, group in stations.groupby("ligne"):
        group_sorted = group.sort_values("ordre")
        previous = None
        for _, row in group_sorted.iterrows():
            node_id = row['station_key'] + "_" + str(row['ligne'])
            if previous is not None:
                prev_id = previous['station_key'] + "_" + str(previous['ligne'])
                coord1 = (previous['latitude'], previous['longitude'])
                coord2 = (row['latitude'], row['longitude'])
                if pd.notnull(coord1[0]) and pd.notnull(coord1[1]) and pd.notnull(coord2[0]) and pd.notnull(coord2[1]):
                    distance = geodesic(coord1, coord2).meters
                else:
                    distance = None
                G.add_edge(
                    prev_id, node_id,
                    type="adjacence",
                    ligne=ligne,
                    distance=distance
                )
            previous = row

    # -- Ajout des arêtes de correspondance (synonymes) --
    stations_by_key = stations.groupby('station_key')
    for station_key, group in stations_by_key:
        node_ids = [row['station_key'] + "_" + str(row['ligne']) for _, row in group.iterrows()]
        for i, node_a in enumerate(node_ids):
            for node_b in node_ids[i+1:]:
                G.add_edge(node_a, node_b, type="correspondance", ligne=None, distance=0)

    print(f"Graphe créé avec {G.number_of_nodes()} noeuds et {G.number_of_edges()} arêtes.")

    # -- Export des arêtes pour debug --
    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "type": data.get('type', 'adjacence'),
            "ligne": data.get('ligne', None),
            "distance_m": data.get('distance', None)
        })
    edges_df = pd.DataFrame(edges)
    edges_df.to_csv(os.path.join(DATA_DIR, "graph_edges.csv"), index=False)
    print("Arêtes sauvegardées dans graph_edges.csv")

    # -- Sauvegarde du graphe en pickle --
    with open(os.path.join(DATA_DIR, "graph_blobia.gpickle"), "wb") as f:
        pickle.dump(G, f)    
    print("Graphe sauvegardé en pickle : graph_blobia.gpickle")

    # -- Visualisation rapide --
    edges_with_distance = [
        (u, v) for u, v, d in G.edges(data=True)
        if G.nodes[u].get('latitude') is not None and G.nodes[u].get('longitude') is not None
        and G.nodes[v].get('latitude') is not None and G.nodes[v].get('longitude') is not None
    ]
    G_sub = G.edge_subgraph(edges_with_distance).copy()
    pos = {
        node: (G_sub.nodes[node]['longitude'], G_sub.nodes[node]['latitude'])
        for node in G_sub.nodes
    }

    plt.figure(figsize=(12, 12))
    nx.draw(G_sub, pos, node_size=10, node_color='red', edge_color='gray', with_labels=False)
    plt.title("Visualisation rapide du réseau métro/RER IDF (Blob IA)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

if __name__ == "__main__":
    build_nodes()
    build_graph()
