def format_route(result, i=None):
    # result = dict unique, ou list[dict]
    def fmt_one(res, num=None):
        out = []
        if num is not None:
            out.append(f"\n--- Trajet #{num+1} ---\n")
        out.append("=== Itinéraire optimal ===\n")
        bloc = []
        last_line = None
        for (station_key, line) in res["path"]:
            # On ne normalise que pour les RER ("RER C 1" → "RER C"), pas pour le métro !
            if line.startswith("RER"):
                line_display = " ".join(line.split()[:2])
            else:
                line_display = line
            if last_line is None:
                bloc = [station_key]
                last_line = line_display
            elif line_display == last_line:
                bloc.append(station_key)
            else:
                out.append(f"{last_line}: " + " - ".join(bloc))
                bloc = [station_key]
                last_line = line_display
        out.append(f"{last_line}: " + " - ".join(bloc))
        out.append("")
        out.append(f"Score du chemin         : {res['score']:.3f}")
        out.append(f"Nombre d’arrêts         : {res['nb_stations']}")
        out.append(f"Affluence moyenne       : {res['affluence_moyenne']:.4f}")
        out.append(f"Affluence max           : {res['affluence_max']:.4f}")
        out.append(f"Stations affluence max  : {', '.join(res['stations_affluence_max'])}")
        
        return "\n".join(out)

    if isinstance(result, list):
        return "\n\n".join([fmt_one(res, i) for i, res in enumerate(result)])
    else:
        return fmt_one(result)
