import heapq
from collections import defaultdict

def normalize_line(line):
    parts = str(line).upper().split()
    if parts[0] in {"RER", "METRO"} and len(parts) > 1:
        return f"{parts[0]} {parts[1]}"
    return str(line).upper()

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
    return_all_explored=False
):

    if curseur == 1:
        alpha = 3.5
        beta  = 0.01
        gamma = 3.0
    elif curseur == 10:
        alpha = 0.01
        beta  = 6.0
        gamma = 0.05
    else:
        alpha = max(0.01, 1.5 - 0.16*curseur)
        beta  = 0.05 + 1.7 * ((curseur-1)/9)**2.1
        gamma = max(0.01, 1.0 - 0.11*curseur)

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
    explored_paths = []

    it = 0
    while front and it < max_iter and len(finals) < topk * 5:
        it += 1
        score, node, path, affluences, lignes, visits = heapq.heappop(front)
        visits = visits.copy()
        visits[G.nodes[node]['station_key']] += 1

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
            succ_station = G.nodes[succ]['station_key']

            # ------------- FILTRE ANTI-BOUCLE -----------------
            potential_path = path + [succ]
            stations_logiques = [(G.nodes[n]['station_key'], normalize_line(G.nodes[n]['ligne'])) for n in potential_path]

            # 1. Pas plus de 2 passages par station (toutes lignes confondues)
            if [G.nodes[n]['station_key'] for n in potential_path].count(succ_station) > 2:
                continue

            # 2. Interdit de repasser sur même station avec même ligne logique
            if stations_logiques.count((succ_station, normalize_line(succ_line))) > 1:
                continue

            # 3. Interdit triple passage d'affilée même station
            if len(potential_path) >= 3:
                if (G.nodes[potential_path[-1]]['station_key'] == G.nodes[potential_path[-2]]['station_key'] == G.nodes[potential_path[-3]]['station_key']):
                    continue

            # 4. Interdit "changement de ligne logique" sans changement effectif (ex : RER C 1 → RER C 2)
            if len(path) >= 1:
                last_station = G.nodes[path[-1]]['station_key']
                last_logique = normalize_line(G.nodes[path[-1]]['ligne'])
                if last_station == succ_station and last_logique == normalize_line(succ_line) and succ_line != lignes[-1]:
                    continue
            # ------------- FIN FILTRE ANTI-BOUCLE --------------

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

    def stations_sequence(path):
        return tuple([G.nodes[n]['station_key'] for n in path])

    unique_routes = {}
    for tup in sorted(finals, key=lambda x: x[0]):
        seq = stations_sequence(tup[2])
        if seq not in unique_routes:
            unique_routes[seq] = tup

    top_routes = list(unique_routes.values())[:3]

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
        for r in explored_paths:
            if "raw_path" not in r:
                r["raw_path"] = r.get("path", None)
        return results, explored_paths
    else:
        return results
