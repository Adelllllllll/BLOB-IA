import streamlit as st
import pandas as pd
import pickle
import os
import re
import numpy as np
import plotly.graph_objects as go
import networkx as nx


from blobia.mapping import normalize_name, find_stations_near_monument
from affluence_builder.get_affluence import get_affluence_mapping_from_file
from blobia.route import find_best_route
from blobia.show_route import format_route


# ----------- Fonctions utilitaires cache et fichiers -----------

@st.cache_data(show_spinner="Chargement du graphe…")
def load_graph(graph_path):
    with open(graph_path, "rb") as f:
        return pickle.load(f)

@st.cache_data(show_spinner="Chargement de l'affluence…")
def load_affluence(affluence_path, jour, heure):
    return get_affluence_mapping_from_file(affluence_path, jour, heure)

@st.cache_data(show_spinner="Chargement des stations…")
def load_stations(stations_path):
    df = pd.read_csv(stations_path)
    df["station_key"] = df["station_key"].astype(str)
    return df[["station", "station_key"]].drop_duplicates()

@st.cache_data(show_spinner="Chargement des monuments…")
def load_monuments(monuments_path):
    df = pd.read_csv(monuments_path, encoding='cp1252')
    return df[["Monument"]].drop_duplicates().sort_values("Monument")

@st.cache_data(show_spinner="Chargement des coordonnées…")
def load_graph_nodes(graph_nodes_path):
    df = pd.read_csv(graph_nodes_path)
    df["gare_key"] = df["gare_key"].astype(str)
    return df

def format_affluence(val):
    try:
        return f"{round(float(val)*100, 1)}"
    except:
        return "?"

def extract_trajet_info(txt):
    txt = re.sub(
        r"Score du chemin *: *[\d\.]+ +Nombre d’arrêt[s]? *: *[\d\?]+ +Affluence moyenne *: *[\d\.]+ +Affluence max *: *[\d\.]+ +Stations affluence max *:.*(\n)?",
        "", txt
    )
    txt = txt.replace("=== Itinéraire optimal ===", "").strip()
    lines = []
    for l in txt.split('\n'):
        l = l.strip()
        if (l.startswith("METRO") or l.startswith("RER")) and ':' in l:
            lines.append(l)
    itineraire = "<br>".join(lines)

    nb_arrets = re.search(r"Nombre d’arrêt[s]? *: *([\d\?]+)", txt)
    nb_arrets = nb_arrets.group(1) if nb_arrets else "?"

    aff_moy = re.search(r"Affluence moyenne *: *([\d\.]+)", txt)
    aff_moy = format_affluence(aff_moy.group(1)) if aff_moy else "?"

    aff_max = re.search(r"Affluence max *: *([\d\.]+)", txt)
    aff_max = format_affluence(aff_max.group(1)) if aff_max else "?"

    st_aff_max = re.search(r"Stations affluence max *: *(.*)", txt)
    st_aff_max = st_aff_max.group(1).replace("[","").replace("]","").replace("'", "") if st_aff_max else "?"

    score = re.search(r"Score du chemin *: *([\d\.]+)", txt)
    score = f"{float(score.group(1)):.1f}" if score else "?"

    return itineraire, nb_arrets, aff_moy, aff_max, st_aff_max, score

# ----------- Chemins fichiers -----------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
GRAPH_PATH = os.path.join(DATA_DIR, "graph_blobia.gpickle")
AFFLUENCE_PATH = os.path.join(DATA_DIR, "Stations_IDF_aligned_affluence.csv")
STATIONS_PATH = os.path.join(DATA_DIR, "Stations_IDF_aligned.csv")
MONUMENTS_PATH = os.path.join(DATA_DIR, "monuments.csv")
GRAPH_NODES_PATH = os.path.join(DATA_DIR, "graph_nodes.csv")

# ----------- Couleurs officielles lignes métro/RER -----------
LINE_COLORS = {
    "METRO 1": [255, 209, 0],        # Jaune éclatant
    "METRO 2": [0, 172, 238],        # Bleu azur
    "METRO 3": [137, 179, 62],       # Vert vif
    "METRO 3bis": [117, 200, 171],   # Vert d'eau
    "METRO 4": [234, 26, 126],       # Rose fuchsia
    "METRO 5": [238, 134, 28],       # Orange franc
    "METRO 6": [123, 206, 210],      # Bleu lagon
    "METRO 7": [207, 97, 172],       # Rose mauve
    "METRO 7bis": [117, 195, 187],   # Bleu vert pastel
    "METRO 8": [154, 104, 183],      # Violet vif
    "METRO 9": [202, 174, 108],      # Ocre doré
    "METRO 10": [240, 206, 74],      # Jaune doré
    "METRO 11": [173, 100, 44],      # Brun caramel
    "METRO 12": [27, 180, 129],      # Vert menthe
    "METRO 13": [135, 177, 71],      # Vert pomme
    "METRO 14": [152, 80, 180],      # Violet profond
    "RER A": [228, 0, 43],           # Rouge RATP
    "RER B": [0, 111, 184],          # Bleu RATP
    "RER C": [241, 196, 0],          # Jaune RATP
    "RER D": [42, 167, 74],          # Vert RATP
    "RER E": [211, 68, 149],         # Violet Magenta
}

# ----------- Fonction d'affichage de la carte Plotly -----------

def plot_itinerary_on_map(coords, trajet_name="Itinéraire"):
    df = pd.DataFrame(coords)
    fig = go.Figure()

    # Tracer les arrêtes (couleur selon la ligne, inchangé)
    for i in range(len(df) - 1):
        line_name = df.loc[i, "line"]
        color_rgb = LINE_COLORS.get(line_name, [0, 0, 0])
        fig.add_trace(go.Scattermapbox(
            lon=[df.loc[i, "lon"], df.loc[i + 1, "lon"]],
            lat=[df.loc[i, "lat"], df.loc[i + 1, "lat"]],
            mode='lines',
            line=dict(width=5, color=f"rgb{tuple(color_rgb)}"),
            hoverinfo='none',
            showlegend=False
        ))

    # Points noirs plus petits pour chaque arrêt, nom à droite
    fig.add_trace(go.Scattermapbox(
        lon=df["lon"],
        lat=df["lat"],
        mode="markers+text",
        marker=dict(
            size=10,      # <-- plus petit !
            color='black',
            opacity=0.95,
        ),
        text=df["name"],
        textposition="middle right",  # nom à droite du point
        textfont=dict(size=13, color="black", family="Arial Black"),
        hoverinfo="text",
        hovertext=df["name"],
        showlegend=False
    ))

    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=df["lat"].mean(), lon=df["lon"].mean()),
            zoom=12.1,
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=550,
        showlegend=False,
    )
    return fig


# ----------- PAGE : Carte Graphe Complet -----------

def extract_grouped_line(line):
    """
    Retourne la ligne groupée : 
    Ex : "RER C 2" → "RER C", "METRO 7bis" → "METRO 7bis", "METRO 7" → "METRO 7"
    """
    line = str(line)
    tokens = line.split()
    if not tokens:
        return line
    if tokens[0] == "METRO":
        # METRO 7bis ou METRO 7 etc.
        if len(tokens) > 1 and "bis" in tokens[1]:
            return f"{tokens[0]} {tokens[1]}"
        elif len(tokens) > 1:
            return f"{tokens[0]} {tokens[1]}"
        else:
            return tokens[0]
    elif tokens[0] == "RER" and len(tokens) > 1:
        return f"{tokens[0]} {tokens[1]}"
    else:
        return line

import pickle
import plotly.graph_objects as go

def afficher_carte_reseau():
    # Chargement du graphe picklé
    with open(GRAPH_PATH, "rb") as f:
        G = pickle.load(f)

    # Liste groupée des lignes (ex : METRO 1, RER A, RER C)
    all_grouped_lines = set()
    for u, v, data in G.edges(data=True):
        if "ligne" in data and data["ligne"] is not None:
            grouped = extract_grouped_line(data["ligne"])
            all_grouped_lines.add(grouped)
    all_grouped_lines = sorted(all_grouped_lines)

    default_lignes = ["METRO 1"] if "METRO 1" in all_grouped_lines else ([all_grouped_lines[0]] if all_grouped_lines else [])

    st.sidebar.markdown("### Lignes à afficher")
    selected_lignes = []
    for l in all_grouped_lines:
        checked = l in default_lignes
        if st.sidebar.checkbox(l, value=checked, key=f"cb_{l}"):
            selected_lignes.append(l)

    if not selected_lignes:
        st.warning("Sélectionne au moins une ligne pour afficher le graphe.")
        st.stop()

    fig = go.Figure()

    # Ajout des arêtes (avec filtre groupé)
    for u, v, d in G.edges(data=True):
        line_full = str(d.get('ligne', ''))
        grouped = extract_grouped_line(line_full)
        if grouped not in selected_lignes:
            continue

        u_data = G.nodes[u]
        v_data = G.nodes[v]
        color_rgb = LINE_COLORS.get(grouped, [0,0,0])
        fig.add_trace(go.Scattermapbox(
            lon=[u_data['longitude'], v_data['longitude']],
            lat=[u_data['latitude'], v_data['latitude']],
            mode='lines',
            line=dict(width=3, color=f"rgb{tuple(color_rgb)}"),
            hoverinfo='none',
            showlegend=False
        ))

    # Ajout des noeuds (stations)
    all_nodes = set()
    for u, v, d in G.edges(data=True):
        line_full = str(d.get('ligne', ''))
        grouped = extract_grouped_line(line_full)
        if grouped in selected_lignes:
            all_nodes.add(u)
            all_nodes.add(v)
    lats = [G.nodes[n]['latitude'] for n in all_nodes]
    lons = [G.nodes[n]['longitude'] for n in all_nodes]
    texts = [n.split("_")[0] for n in all_nodes]
    fig.add_trace(go.Scattermapbox(
        lon=lons, lat=lats,
        mode='markers',
        marker=dict(size=6, color='black'),
        text=texts,
        hoverinfo='text',
        showlegend=False
    ))
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=48.85, lon=2.35),  # Paris
            zoom=9,
        ),
        margin=dict(l=0, r=0, t=20, b=0),
        height=700,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ----------- Interface Streamlit -----------

if "selected_trajet_idx" not in st.session_state:
    st.session_state['selected_trajet_idx'] = -1
if "result" not in st.session_state:
    st.session_state['result'] = None

with st.sidebar:
    col_logo, col_title = st.columns([2,6])
    with col_logo:
        st.image("images-interface/logo.png", width=100)
    with col_title:
        st.markdown(
            "<div style='display: flex; align-items: center; height: 100%;'>"
            "<span style='font-size:1.3em; margin-top:25px;font-weight:700;'>Sélectionne tes critères</span>"
            "</div>",
            unsafe_allow_html=True
        )


page = st.sidebar.radio(
    "Aller vers…",
    ["Calcul d'itinéraire", "Carte graphe complet"],
    index=0,
    key="page_select"
)

if page == "Calcul d'itinéraire":
    st.image("images-interface/Titre.png", use_column_width=True)   

    stations_df = load_stations(STATIONS_PATH)
    monuments_df = load_monuments(MONUMENTS_PATH)
    graph_nodes_df = load_graph_nodes(GRAPH_NODES_PATH)
    station_affichage_to_key = dict(zip(stations_df["station"], stations_df["station_key"]))

    with st.sidebar.form("params_form"):
        station_depart_affichage = st.selectbox(
            "Station de départ",
            stations_df["station"].sort_values().tolist(),
            key="station_depart"
        )
        monument_arrivee = st.selectbox(
            "Monument d'arrivée",
            monuments_df["Monument"].tolist(),
            key="monument_arrivee"
        )
        acces_pmr = ['Oui', 'Non']
        acces = st.selectbox("Accessible pour PMR", acces_pmr, index=0, key="acces")
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        jour = st.selectbox("Jour du trajet", jours, index=0, key="jour")
        heure = st.slider("Heure du trajet", 0, 23, 8, key="heure")
        
        # Slider sans label
        curseur = st.slider("Curseur de personnalisation (rapidité / affluence)", 1, 10, 5, key="curseur")

        # Images + labels dessous
        col_left, col_center, col_right = st.columns([1, 4, 1])
        with col_left:
            st.image("images-interface/blob_rapide.png", width=60)
            st.markdown("<div style='text-align:center; font-size:0.85em'></div>", unsafe_allow_html=True)
        with col_center:
            st.markdown("")
        with col_right:
            st.image("images-interface/blob_zen.png", width=60)
            st.markdown("<div style='text-align:center; font-size:0.85em'></div>", unsafe_allow_html=True)

            
        # Bouton avec blob happy à côté
        col_btn, col_img = st.columns([2,1])
        with col_btn:
            submit = st.form_submit_button("Calculer l’itinéraire")


    if submit:
        st.session_state['selected_trajet_idx'] = -1
        try:
            with st.spinner("Chargement du réseau et des données…"):
                G = load_graph(GRAPH_PATH)
                afflu_map = load_affluence(AFFLUENCE_PATH, jour, heure)

            station_depart_key = station_affichage_to_key[station_depart_affichage]
            stations_nodes = [n for n, d in G.nodes(data=True) if d.get("station_key", "") == station_depart_key]
            if not stations_nodes:
                st.error(f"Station de départ « {station_depart_affichage} » (clé: {station_depart_key}) introuvable dans le réseau.")
                st.stop()

            arr_candidates = find_stations_near_monument(
                monument_arrivee,
                rayon_m=900,
                monuments_csv=MONUMENTS_PATH,
                stations_csv=GRAPH_NODES_PATH
            )
            afflu_df = pd.read_csv(AFFLUENCE_PATH)
            line_to_station = dict()
            for st_key, dist in arr_candidates:
                for _, row in afflu_df[afflu_df["station_key"].apply(lambda x: normalize_name(str(x)) == normalize_name(st_key))].iterrows():
                    line = str(row["ligne"])
                    if (line not in line_to_station) or (dist < line_to_station[line][1]):
                        line_to_station[line] = (normalize_name(st_key), dist)
            arr_station_keys = [s for s, _ in line_to_station.values()]
            arr_lines = [line for line in line_to_station.keys()]

            arr_node_ids = []
            for node, data in G.nodes(data=True):
                skey = normalize_name(data.get("station_key", ""))
                line = str(data.get("ligne", ""))
                if skey in arr_station_keys and line in arr_lines:
                    arr_node_ids.append(node)

            if not arr_station_keys:
                st.error(f"Aucune station d’arrivée trouvée près du monument « {monument_arrivee} ».")
                st.session_state['result'] = None
                st.stop()

            result = find_best_route(
                G=G,
                affluence_mapping=afflu_map,
                station_depart=station_depart_key,
                list_stations_arrivee=arr_station_keys,
                curseur=curseur,
                verbose=False
            )
            st.session_state['result'] = result
            st.session_state['afflu_map'] = afflu_map
        except Exception as e:
            import traceback
            st.error(f"Erreur lors du calcul : {e}\n\n{traceback.format_exc()}")
            st.session_state['result'] = None

    result = st.session_state.get('result', None)
    afflu_map = st.session_state.get('afflu_map', {})  # clé: station_key
    if result:
        for i, trajet in enumerate(result):
            if isinstance(trajet, dict):
                itineraire_raw = trajet.get('itineraire', format_route(trajet))
                itineraire_html, nb_arrets, aff_moy, aff_max, st_aff_max, score = extract_trajet_info(
                    itineraire_raw + "\n"
                    + f"Nombre d’arrêts : {trajet.get('arrets', '?')}\n"
                    + f"Affluence moyenne : {trajet.get('affluence_moyenne', '?')}\n"
                    + f"Affluence max : {trajet.get('affluence_max', '?')}\n"
                    + f"Stations affluence max : {trajet.get('stations_affluence_max', '?')}\n"
                    + f"Score du chemin : {trajet.get('score', '?')}\n"
                )
            else:
                itineraire_html, nb_arrets, aff_moy, aff_max, st_aff_max, score = extract_trajet_info(format_route(trajet))

            with st.container():
                # Ligne image + titre
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.image("images-interface/blob_check.png", width=65)
                with col2:
                    st.markdown(
                        f"<h3 style='margin-top:0;margin-bottom:10px;display:inline-block;vertical-align:middle;'>"
                        f"Trajet #{i+1}{' (sélectionné)' if st.session_state.get('selected_trajet_idx', -1) == i else ''}</h3>",
                        unsafe_allow_html=True
                    )

                # Ensuite, ton markdown principal sans la ligne <h3> !
                st.markdown(
                    f"""
                    <div style="background-color:#F0F6FF;padding:22px 28px 10px 28px;margin-bottom:20px;
                        border-radius:18px;box-shadow:0 2px 8px #0001">
                        <div style="font-size:1.13em;margin-bottom:14px;">
                            <b>{itineraire_html}</b>
                        </div>
                        <ul style="margin-top:0;margin-bottom:10px;line-height:1.7;">
                            <li><b>Nombre d’arrêts :</b> {nb_arrets}</li>
                            <li><b>Affluence moyenne :</b> {aff_moy}</li>
                            <li><b>Affluence max :</b> {aff_max}</li>
                            <li><b>Stations affluence max :</b> {st_aff_max}</li>
                        </ul>
                        <div style="font-size:0.93em;color:#555;margin-top:8px;text-align:left;">
                            <b>Score :</b> {score}
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )

                btn_key = f"select_trajet_{i}"
                if st.button("Sélectionner ce trajet et afficher la carte", key=btn_key):
                    st.session_state['selected_trajet_idx'] = i

                if st.session_state.get('selected_trajet_idx', -1) == i:
                    st.markdown("### 🗺️ Carte de l’itinéraire sélectionné")
                    path = trajet.get("path", [])
                    coords = []
                    for stop in path:
                        station_key = str(stop[0])
                        line = str(stop[1])
                        matches = graph_nodes_df[graph_nodes_df["gare_key"].apply(lambda x: normalize_name(str(x)) == normalize_name(station_key))]
                        if not matches.empty:
                            lat = matches.iloc[0]["latitude"]
                            lon = matches.iloc[0]["longitude"]
                            name = matches.iloc[0]["nom_so_gar"]
                            # -- Affluence extraction --
                            afflu = 0.0
                            if afflu_map:
                                aff_key = f"{station_key}/{line}"
                                if aff_key in afflu_map:
                                    afflu = afflu_map[aff_key]
                                elif station_key in afflu_map:
                                    afflu = afflu_map[station_key]
                            coords.append({"lat": lat, "lon": lon, "line": line, "name": name, "affluence": afflu})

                    if len(coords) >= 2:
                        fig = plot_itinerary_on_map(coords, trajet_name=f"Trajet #{i+1}")
                        st.plotly_chart(fig, use_container_width=True)
                    elif coords:
                        st.warning("Impossible d'afficher le trajet : il manque des coordonnées pour certains arrêts.")
                    else:
                        st.error("Aucune coordonnée trouvée pour l'itinéraire.")

    else:
        if submit:
            st.warning("Aucun trajet n'a pu être trouvé entre ces points pour vos critères.")


elif page == "Carte graphe complet":
    afficher_carte_reseau()
