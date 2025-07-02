import os
import random
import heapq
import math
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import pickle

def normalize_name(name):
    return name.lower().replace('-', ' ').replace('’', "'").replace("œ", "oe").replace('é', 'e').replace('ê', 'e').replace('è', 'e').replace('à', 'a').replace('â', 'a').replace('î', 'i').replace('ï', 'i').replace('ç', 'c')

def find_stations_near_monument(monument, rayon_m=900, monuments_csv=None, stations_csv=None):
    monuments = pd.read_csv(monuments_csv)
    stations = pd.read_csv(stations_csv)
    monuments['name_norm'] = monuments['Monument'].map(normalize_name)
    stations['name_norm'] = stations['nom_so_gar'].map(normalize_name)
    monument_norm = normalize_name(monument)
    mrow = monuments[monuments['name_norm'].str.contains(monument_norm)]
    if len(mrow) == 0:
        print(f"[WARN] Monument '{monument}' non trouvé.")
        return []
    coord_m = (mrow.iloc[0]['Latitude'], mrow.iloc[0]['Longitude'])
    near = []
    for i, row in stations.iterrows():
        d = geodesic(coord_m, (row['Latitude'], row['Longitude'])).meters
        if d < rayon_m:
            near.append(row['gare_key'])
    return near

def find_depart_nodes(G, station_str):
    norm = normalize_name(station_str)
    nodes = [n for n in G.nodes if norm in normalize_name(G.nodes[n]['name'])]
    if not nodes:
        print(f"[WARN] Station '{station_str}' non trouvée dans le graphe.")
    return nodes

def visu_blob_solver(G, affluence_map, nodes_depart, nodes_arrivee, curseur=5, max_iter=50000, topk=10):
    # Pondérations : à adapter à ta logique (peux raffiner si besoin)
    alpha = 0.4 + 0.08 * curseur  # distance (nombre d'arrêts)
    beta = 0.1 + 0.04 * curseur   # affluence
    gamma = 0.16 + 0.04 * curseur # changement de ligne

    print(f"[DEBUG] VISU Params: alpha={alpha:.2f}, beta={beta:.2f}, gamma={gamma:.2f}")

    front = []
    heapq.heapify(front)
    for dep in nodes_depart:
        data = G.nodes[dep]
        score_init = 0.0
        aff_init = affluence_map.get((data['station_key'], data['ligne']), 0.2)
        heapq.heappush(front, (score_init, dep, [dep], [aff_init], [data['ligne']], set(), 0))

    finals = []
    explored_paths = []  # Toutes les routes explorées

    for it in range(max_iter):
        if not front:
            break
        score, node, path, affluences, lignes, visited_set, nb_chg = heapq.heappop(front)
        explored_paths.append((score, node, path.copy(), affluences.copy(), lignes.copy(), nb_chg, node in nodes_arrivee))
        if node in nodes_arrivee:
            finals.append((score, node, path.copy(), affluences.copy(), lignes.copy(), nb_chg))
            if len(finals) >= topk:
                break
        visited = visited_set.copy()
        visited.add(node)
        for succ in G.neighbors(node):
            if succ in path:
                continue
            succ_line = G.nodes[succ]['ligne']
            succ_aff = affluence_map.get((G.nodes[succ]['station_key'], succ_line), 0.2)
            chg = nb_chg + (succ_line != lignes[-1])
            aff_moy = (sum(affluences) + succ_aff) / (len(affluences) + 1)
            new_score = alpha * (len(path) + 1) + beta * aff_moy + gamma * chg
            heapq.heappush(front, (
                new_score,
                succ,
                path + [succ],
                affluences + [succ_aff],
                lignes + [succ_line],
                visited,
                chg
            ))

    # Reformat all explored paths as dicts
    explored_routes = []
    for tup in explored_paths:
        score, node, path, affluences, lignes, nb_chg, finished = tup
        explored_routes.append({
            "score": score,
            "raw_path": path,
            "raw_lignes": lignes,
            "final": finished,
            "nb_changements": nb_chg,
        })

    # finals = completed paths only
    finals_sorted = sorted([{
        "score": score,
        "raw_path": path,
        "raw_lignes": lignes,
        "final": True,
        "nb_changements": nb_chg,
    } for (score, node, path, affluences, lignes, nb_chg) in finals], key=lambda x: x["score"])

    return finals_sorted, explored_routes

def plot_routes_on_graph(G, best_trajs, explored, max_explored=3000):
    # Use latitude/longitude for pos
    pos = {}
    for n in G.nodes:
        node = G.nodes[n]
        if 'latitude' in node and 'longitude' in node:
            pos[n] = (node['longitude'], node['latitude'])
        elif 'lat' in node and 'lon' in node:
            pos[n] = (node['lon'], node['lat'])
        else:
            continue

    plt.figure(figsize=(15, 8))
    # Noeuds gris
    nx.draw_networkx_nodes(G, pos, alpha=0.13, node_color='gray', node_size=20)
    # Arêtes grises fines (uniquement pour noeuds affichés)
    edgelist = [(u, v) for u, v in G.edges if u in pos and v in pos]
    nx.draw_networkx_edges(G, pos, edgelist=edgelist, alpha=0.05, edge_color='gray', width=0.5)

    # Jaune = chemins explorés non aboutis
    for r in explored[:max_explored]:
        if not r["final"]:
            path = r["raw_path"]
            path = [n for n in path if n in pos]
            if len(path) > 1:
                nx.draw_networkx_edges(G, pos, edgelist=[(path[i], path[i+1]) for i in range(len(path)-1)], width=1.5, edge_color="gold", alpha=0.14)

    # Orange = chemin finis non optimaux
    if len(best_trajs) > 1:
        for r in best_trajs[1:]:
            path = r["raw_path"]
            path = [n for n in path if n in pos]
            if len(path) > 1:
                nx.draw_networkx_edges(G, pos, edgelist=[(path[i], path[i+1]) for i in range(len(path)-1)], width=2.5, edge_color="orange", alpha=0.33)

    # Rouge épais = chemin optimal
    if best_trajs:
        r = best_trajs[0]
        path = r["raw_path"]
        path = [n for n in path if n in pos]
        if len(path) > 1:
            nx.draw_networkx_edges(G, pos, edgelist=[(path[i], path[i+1]) for i in range(len(path)-1)], width=4, edge_color="red", alpha=0.7)

    plt.title("Chemins explorés (jaune), aboutis (orange), optimal (rouge) - Algo Blob IA", fontsize=22)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

def main():
    # ==== CONFIGURATION RAPIDE ====
    root = os.path.dirname(__file__)
    graph_path = os.path.abspath(os.path.join(root, "../data/graph_blobia.gpickle"))
    affluence_csv = os.path.abspath(os.path.join(root, "../data/Stations_IDF_aligned_affluence.csv"))
    monuments_csv = os.path.abspath(os.path.join(root, "../data/monuments.csv"))
    stations_csv = os.path.abspath(os.path.join(root, "../data/emplacement_des_gares_idf_aligned.csv"))

    DEPART_STR = "aeroport d'orly"
    MONUMENT_STR = "Jardin de la Tour Effeil"
    DAY = "lundi"
    HOUR = "8h"
    CURSEUR = 5

    print(f"==== VISUALISATION TRAJET BLOB IA ====")
    print(f"Départ : {DEPART_STR} | Arrivée : {MONUMENT_STR} | Jour : {DAY} | Heure : {HOUR} | Curseur : {CURSEUR}")

    # Chargement du graphe
    print("[DEBUG] Chargement du graphe...")
    with open(graph_path, "rb") as f:
        G = pickle.load(f)

    # Trouver noeuds de départ
    nodes_dep = find_depart_nodes(G, DEPART_STR)
    print(f"[DEBUG] Noeuds de départ considérés : {nodes_dep}")

    # Trouver noeuds proches du monument
    arr_candidates = find_stations_near_monument(MONUMENT_STR, rayon_m=900, monuments_csv=monuments_csv, stations_csv=stations_csv)
    print(f"[DEBUG] Stations proches considérées : {arr_candidates}")

    # Les correspondances du graphe utilisent station_key
    nodes_arr = [n for n in G.nodes if G.nodes[n]['station_key'] in arr_candidates]

    # Mapping affluence
    affluence_df = pd.read_csv(affluence_csv)
    affluence_map = {}
    for _, row in affluence_df.iterrows():
        key = (row['station_key'], row['ligne'])
        affluence_map[key] = row['affluence_' + DAY + '_' + HOUR]

    # Lancement du solver de visualisation
    best_trajs, explored = visu_blob_solver(G, affluence_map, nodes_dep, nodes_arr, curseur=CURSEUR, max_iter=50000, topk=10)
    print(f"[INFO] {len(explored)} chemins explorés au total par l'algo Blob")
    plot_routes_on_graph(G, best_trajs, explored, max_explored=300)

if __name__ == "__main__":
    main()
