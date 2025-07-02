import streamlit as st
import pandas as pd
import pickle
import os
import re

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

# ----------- Interface Streamlit -----------

if "selected_trajet_idx" not in st.session_state:
    st.session_state['selected_trajet_idx'] = -1

st.sidebar.title("🗺️ Sélectionne tes critères")
page = st.sidebar.radio(
    "Aller vers…",
    ["Calcul d'itinéraire", "À propos"],
    index=0,
    key="page_select"
)

if page == "Calcul d'itinéraire":
    st.title("🚇 Calcul d'itinéraire BLOB-IA")

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
        jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        jour = st.selectbox("Jour du trajet", jours, index=0, key="jour")
        heure = st.slider("Heure du trajet", 0, 23, 8, key="heure")
        curseur = st.slider("Curseur : 1 (Rapide) → 10 (Affluence minimale)", 1, 10, 5, key="curseur")
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

            # -------- LOGIQUE DU MAIN pour l'arrivée --------
            arr_candidates = find_stations_near_monument(
                monument_arrivee,
                rayon_m=900,
                monuments_csv=MONUMENTS_PATH,
                stations_csv=GRAPH_NODES_PATH
            )
            afflu_df = pd.read_csv(AFFLUENCE_PATH)
            line_to_station = dict()  # {ligne: (station_key, distance)}
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
                st.stop()

            result = find_best_route(
                G=G,
                affluence_mapping=afflu_map,
                station_depart=station_depart_key,
                list_stations_arrivee=arr_station_keys,
                curseur=curseur,
                verbose=False
            )

            # ----------- Affichage des trajets et boutons -----------

            if result:
                st.markdown('<span style="font-size:1.1em;color:#21ba45;font-weight:600;">✅ Résultats trouvés !</span>', unsafe_allow_html=True)
                for i, trajet in enumerate(result):
                    # Calcul des variables d'affichage pour chaque trajet
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
                        st.markdown(
                            f"""
                            <div style="background-color:#F0F6FF;padding:22px 28px 10px 28px;margin-bottom:20px;
                                border-radius:18px;box-shadow:0 2px 8px #0001">
                                <h3 style="margin-top:0;margin-bottom:10px;">🚇 Trajet #{i+1}{' (sélectionné)' if st.session_state.get('selected_trajet_idx', -1) == i else ''}</h3>
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

                        # Affiche la map UNIQUEMENT pour le trajet sélectionné
                        if st.session_state.get('selected_trajet_idx', -1) == i:
                            st.markdown("### 🗺️ Carte de l’itinéraire sélectionné")
                            path = trajet.get("path", [])
                            coords = []
                            for stop in path:
                                station_key = str(stop[0])
                                matches = graph_nodes_df[graph_nodes_df["gare_key"].apply(lambda x: normalize_name(str(x)) == normalize_name(station_key))]
                                if not matches.empty:
                                    lat = matches.iloc[0]["latitude"]
                                    lon = matches.iloc[0]["longitude"]
                                    coords.append({"lat": lat, "lon": lon})
                            if len(coords) >= 2:
                                st.map(pd.DataFrame(coords))
                            elif coords:
                                st.warning("Impossible d'afficher le trajet : il manque des coordonnées pour certains arrêts.")
                            else:
                                st.error("Aucune coordonnée trouvée pour l'itinéraire.")

            else:
                st.warning("Aucun trajet n'a pu être trouvé entre ces points pour vos critères.")
        except Exception as e:
            import traceback
            st.error(f"Erreur lors du calcul : {e}\n\n{traceback.format_exc()}")

elif page == "À propos":
    st.title("À propos")
    st.markdown("""
    Projet Blob IA — Planificateur de trajets intelligent pour le métro/RER d'Île-de-France.  
    [Ajoute ici ta description, ton équipe, des liens, etc.]

    _Ajoute tes pages dans la sidebar pour enrichir l'application selon tes besoins !_""")
