import heapq
from collections import defaultdict
import random

def normalize_line(line):
    parts = line.upper().split()
    if parts[0] in {"RER", "METRO"}:
        return f"{parts[0]} {parts[1]}"
    return line.upper()

def blob_path_solver(
    G,
    affluence_mapping,
    nodes_depart,
    nodes_arrivee,
    curseur=1,
    verbose=False,
    max_iter=25000,
    max_visites_station=2,
    topk=10,
    return_all_explored=False  # <---- Option pour visu
):
    # Pondérations adaptées, restent progressives mais impactent bien les extrêmes
    alpha = max(0.1, 1.0 - 0.09 * (curseur - 1)) if curseur < 10 else 0.01
    beta = 0.1 + 0.12 * (curseur - 1) if curseur > 1 else 0.01
    gamma = 1.0 - 0.09 * (curseur-1)

    front = []
    heapq.heapify(front)
    for dep in nodes_depart:
        data = G.nodes[dep]
        score_init = 0.0
        aff_init = affluence_mapping.get((data['station_key'], data['ligne']), 0.2)
        visits = defaultdict(int)
        visits[G.nodes[dep]['station_key']] = 1
        heapq.heappush(front, (score_init, dep, [dep], [aff_init], [data['ligne']], visits))

    visited = dict()
    finals = []
    explored_paths = []  # <- pour visu

    it = 0
    while front and it < max_iter and len(finals) < topk * 5:
        it += 1
        score, node, path, affluences, lignes, visits = heapq.heappop(front)
        visits = visits.copy()
        visits[G.nodes[node]['station_key']] += 1

        # Sauvegarde du chemin courant (pour la visu)
        if return_all_explored:
            explored_paths.append({
                "score": score,
                "raw_path": list(path),
                "affluences": list(affluences),
                "lignes": list(lignes)
            })

        if node in nodes_arrivee:
            finals.append((score, node, path, affluences, lignes))
            continue

        key = (node, lignes[-1])
        if key in visited and visited[key] <= score:
            continue
        visited[key] = score

        for succ in G.neighbors(node):
            succ_line = G.nodes[succ]['ligne']
            succ_aff = affluence_mapping.get((G.nodes[succ]['station_key'], succ_line), 0.2)
            # Ne repasse jamais plus de 2 fois par une station, sauf pour une correspondance (ligne différente)
            if visits[G.nodes[succ]['station_key']] >= max_visites_station:
                # Autorise de repasser si changement de ligne
                if succ_line == lignes[-1]:
                    continue
            # Empêche de tourner en rond juste pour baisser l'affluence
            if (normalize_line(succ_line) == normalize_line(lignes[-1])
                and G.nodes[succ]['station_key'] == G.nodes[node]['station_key']
                and succ_line != lignes[-1]):
                continue
            penalty = 0.0
            if succ_line != lignes[-1]:
                penalty += gamma
            nb_arrets = len(path)
            aff_moy = (sum(affluences) + succ_aff) / (len(affluences) + 1)
            new_score = (
                alpha * (nb_arrets + 1) +
                beta * aff_moy +
                penalty
            )
            heapq.heappush(front, (
                new_score,
                succ,
                path + [succ],
                affluences + [succ_aff],
                lignes + [succ_line],
                visits
            ))

    # Filtrage top 3 pour résultat principal
    def stations_sequence(path):
        return tuple([G.nodes[n]['station_key'] for n in path])

    unique_routes = {}
    for tup in sorted(finals, key=lambda x: x[0]):
        seq = stations_sequence(tup[2])
        if seq not in unique_routes:
            unique_routes[seq] = tup

    top_routes = list(unique_routes.values())[:3]  # Top 3 uniques

    # Formatage standard pour main.py
    results = []
    for score, node, path, affluences, lignes in top_routes:
        stations = [G.nodes[n]['name'] for n in path]
        lignes_aff = [normalize_line(G.nodes[n]['ligne']) for n in path]
        aff_moy = sum(affluences) / len(affluences)
        aff_max = max(affluences)
        stations_aff_max = [stations[i] for i, aff in enumerate(affluences) if aff == aff_max]
        changements = [i for i in range(1, len(lignes_aff)) if lignes_aff[i] != lignes_aff[i-1]]
        nb_changements = len(changements)
        path_keys = [(G.nodes[n]['station_key'], lignes_aff[i]) for i, n in enumerate(path)]
        results.append({
            "path": path_keys,
            "score": score,
            "nb_stations": len(path),
            "nb_changements": nb_changements,
            "changements": changements,
            "affluence_moyenne": aff_moy,
            "affluence_max": aff_max,
            "stations_affluence_max": stations_aff_max,
            "raw_path": path,
            "raw_lignes": lignes_aff,
        })

    if return_all_explored:
        # Pour la visu : chaque chemin doit avoir .raw_path
        for r in explored_paths:
            if "raw_path" not in r:
                r["raw_path"] = r.get("path", None)
        return results, explored_paths
    else:
        return results
