import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import PROFILE_JOUR, PROFILE_HEURE

SCORE_MIN = 0.15  # score minimum utilisé à la création

def visualize_graph_dynamique(jour="lundi", heure=8):
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    stations_path = os.path.join(DATA_DIR, 'stations_lignes_coords.csv')
    affluence_path = os.path.join(DATA_DIR, 'Stations_IDF_aligned_affluence.csv')

    stations = pd.read_csv(stations_path)
    stations["station_key"] = stations["station_key"].astype(str).str.strip().str.lower()
    stations["ligne"] = stations["ligne"].astype(str).str.strip()
    afflu = pd.read_csv(affluence_path)
    afflu["station_key"] = afflu["station_key"].astype(str).str.strip().str.lower()
    afflu["ligne"] = afflu["ligne"].astype(str).str.strip()

    afflu_dict = {(row["station_key"], row["ligne"]): row["affluence_score"] for _, row in afflu.iterrows()}

    coef_jour = PROFILE_JOUR.get(jour.lower(), 0.7)
    coef_heure = PROFILE_HEURE.get(int(heure), 0.5)

    G = nx.Graph()
    for _, row in stations.iterrows():
        node_id = row['station_key'] + "_" + str(row['ligne'])
        score_base = afflu_dict.get((row['station_key'], row['ligne']), SCORE_MIN)
        score_dyn = min(1.0, score_base * coef_jour * coef_heure)
        G.add_node(node_id,
                   name=row['station'],
                   ligne=row['ligne'],
                   latitude=row['latitude'],
                   longitude=row['longitude'],
                   affluence_score=score_dyn)


    # --- Visualisation ---
    pos = {node: (data['longitude'], data['latitude']) for node, data in G.nodes(data=True)}
    afflu_scores = [G.nodes[n]["affluence_score"] for n in G.nodes()]

    # Pas de normalisation locale ! On utilise la vraie échelle de 0.15 à 1
    colors_norm = afflu_scores  # gardés dans l’échelle réelle

    plt.figure(figsize=(15, 15))
    nodes = nx.draw_networkx_nodes(G, pos,
                                   node_size=30,
                                   node_color=colors_norm,
                                   cmap=plt.cm.inferno,
                                   alpha=0.85,
                                   vmin=SCORE_MIN, vmax=1.0)  # important pour la comparaison

    nx.draw_networkx_edges(G, pos,
                           edge_color="#888888", alpha=0.3, width=1)
    plt.colorbar(nodes, label="Affluence dynamique (score réel)")

    plt.title(f"Réseau métro/RER Île-de-France – Affluence dynamique\n{jour.capitalize()} à {heure}h")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    visualize_graph_dynamique(jour="lundi", heure=8)
