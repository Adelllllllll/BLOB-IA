import os
import pickle
import pandas as pd
import networkx as nx

from blobia.mapping import normalize_name, find_stations_near_monument
from affluence_builder.get_affluence import get_affluence_mapping_from_file
from blobia.route import find_best_route
from blobia.show_route import format_route

DEPART_STR = "aeroport d'orly"
MONUMENT_STR = "Jardin de la Tour Effeil"
JOUR = "lundi"
HEURE = 8

def main():
    BASE = os.path.dirname(os.path.abspath(__file__))
    graph_path = os.path.join(BASE, "data", "graph_blobia.gpickle")
    affluence_path = os.path.join(BASE, "data", "Stations_IDF_aligned_affluence.csv")
    monuments_csv = os.path.join(BASE, "data", "monuments.csv")
    stations_csv = os.path.join(BASE, "data", "graph_nodes.csv")

    print("==== Planificateur de trajet Métro/RER Blob IA ====\n")
    print(f"Départ : {DEPART_STR} | Arrivée : {MONUMENT_STR} | Jour : {JOUR} | Heure : {HEURE}h\n")
    try:
        curseur = int(input("Curseur 1 (rapide) → 10 (peu d’affluence) : ").strip())
        assert 1 <= curseur <= 10
    except (ValueError, AssertionError):
        print("Erreur : Curseur doit être un entier entre 1 et 10.")
        return

    print("\nChargement du graphe…")
    try:
        with open(graph_path, "rb") as f:
            G = pickle.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement du graphe : {e}")
        return
    try:
        afflu_map = get_affluence_mapping_from_file(affluence_path, JOUR, HEURE)
        afflu_df = pd.read_csv(affluence_path)  # Pour lier station -> ligne
    except Exception as e:
        print(f"Erreur lors du chargement de l'affluence : {e}")
        return

    dep_norm = normalize_name(DEPART_STR)
    dep_node_ids = [n for n, d in G.nodes(data=True) if normalize_name(d.get("station_key", "")) == dep_norm]
    if not dep_node_ids:
        print(f"Départ « {DEPART_STR} » introuvable dans le graphe.")
        return

    # -- Sélection des stations d’arrivée proches du monument --
    try:
        arr_candidates = find_stations_near_monument(
            MONUMENT_STR,
            rayon_m=900,
            monuments_csv=monuments_csv,
            stations_csv=stations_csv
        )
    except Exception as e:
        print(f"Erreur : {e}")
        return

    print(f" Stations proches considérées : {[st for st, _ in arr_candidates]}")

    # Pour chaque station proche, trouve TOUTES ses lignes, ne garde que la plus proche par ligne
    line_to_station = dict()  # {ligne: (station_key, distance)}
    for st, dist in arr_candidates:
        # Pour chaque ligne associée à cette station dans afflu_df
        for _, row in afflu_df[afflu_df["station_key"].apply(lambda x: normalize_name(str(x)) == normalize_name(st))].iterrows():
            line = str(row["ligne"])
            if (line not in line_to_station) or (dist < line_to_station[line][1]):
                line_to_station[line] = (normalize_name(st), dist)

    # On ne garde qu'une station la plus proche par ligne
    arr_station_keys = [s for s, _ in line_to_station.values()]
    arr_lines = [line for line in line_to_station.keys()]

    # On construit les node_ids d'arrivée
    arr_node_ids = []
    arr_debug = []
    for node, data in G.nodes(data=True):
        skey = normalize_name(data.get("station_key", ""))
        line = str(data.get("ligne", ""))
        if skey in arr_station_keys and line in arr_lines:
            arr_node_ids.append(node)
            arr_debug.append(f"{data.get('name', skey)} ({line})")

    if not arr_node_ids:
        print(f"Aucune station d’arrivée trouvée près du monument « {MONUMENT_STR} ».")
        return

    print("\nCalcul du meilleur trajet (algorithme Blob)...")
    result = find_best_route(
        G=G,
        affluence_mapping=afflu_map,
        station_depart=dep_norm,
        list_stations_arrivee=arr_station_keys,
        curseur=curseur,
        verbose=True
    )

    if result:
        for i, r in enumerate(result, 1):
            print(f"\n--- Trajet #{i} ---\n")
            print(format_route(r))
    else:
        print("Aucun trajet trouvé entre les points sélectionnés.")

if __name__ == "__main__":
    main()
