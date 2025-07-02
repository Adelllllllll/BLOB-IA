from blobia.blob_solver import blob_path_solver

def find_best_route(
    G,
    affluence_mapping,
    station_depart,
    list_stations_arrivee,
    curseur=1,
    rayon_m=500,
    verbose=False
):
    # 1. Noeuds départ
    nodes_depart = [n for n, d in G.nodes(data=True) if d['station_key'] == station_depart]
    if not nodes_depart:
        raise ValueError(f"Aucune station de départ trouvée pour '{station_depart}' dans le graphe !")

    # 2. Arrivée
    nodes_arrivee = []
    for s in list_stations_arrivee:
        nodes_arrivee.extend([n for n, d in G.nodes(data=True) if d['station_key'] == s])
    if not nodes_arrivee:
        raise ValueError(f"Aucune station d'arrivée trouvée pour {list_stations_arrivee} !")

    # 3. Appel blob_solver (on récupère plusieurs routes, déjà filtrées)
    results = blob_path_solver(
        G,
        affluence_mapping,
        nodes_depart,
        nodes_arrivee,
        curseur=curseur,
        verbose=verbose,
        max_visites_station=2,
        topk=8
    )
    return results
