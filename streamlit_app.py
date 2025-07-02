import streamlit as st
import pandas as pd
import pickle
import os

from blobia.mapping import normalize_name, find_stations_near_monument
from affluence_builder.get_affluence import get_affluence_mapping_from_file
from blobia.route import find_best_route
from blobia.show_route import format_route

# --- Fonctions utilitaires pour chargement en cache ---
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
    # On retourne toutes les stations, même si doublons (plusieurs lignes par station)
    df["station_key"] = df["station_key"].astype(str)
    return df[["station", "station_key"]].drop_duplicates()

@st.cache_data(show_spinner="Chargement des monuments…")
def load_monuments(monuments_path):
    df = pd.read_csv(monuments_path, encoding='cp1252')  # encodage Windows le plus courant en France
    return df[["Monument"]].drop_duplicates().sort_values("Monument")

# --- Chemins fichiers ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
GRAPH_PATH = os.path.join(DATA_DIR, "graph_blobia.gpickle")
AFFLUENCE_PATH = os.path.join(DATA_DIR, "Stations_IDF_aligned_affluence.csv")
STATIONS_PATH = os.path.join(DATA_DIR, "Stations_IDF_aligned.csv")
MONUMENTS_PATH = os.path.join(DATA_DIR, "monuments.csv")
GRAPH_NODES_PATH = os.path.join(DATA_DIR, "graph_nodes.csv")

# --- Onglets/sidebar ---
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller vers…",
    ["Calcul d'itinéraire", "À propos"],
    index=0,
    key="page_select"
)

# --- Page 1 : Calcul d'itinéraire ---
if page == "Calcul d'itinéraire":
    st.title("🟢 Planificateur de trajet Métro/RER Blob IA")
    st.markdown("Calcule le meilleur trajet selon tes critères : rapidité ou confort d'affluence.")

    # Chargement listes stations/monuments
    stations_df = load_stations(STATIONS_PATH)
    monuments_df = load_monuments(MONUMENTS_PATH)
    # --- mapping affichage -> clé ---
    station_affichage_to_key = dict(zip(stations_df["station"], stations_df["station_key"]))

    with st.form("params_form"):
        # Liste triée des noms "jolis" pour la UI
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
        try:
            with st.spinner("Chargement du réseau et des données…"):
                G = load_graph(GRAPH_PATH)
                afflu_map = load_affluence(AFFLUENCE_PATH, jour, heure)
            # Prend la vraie clé station_key
            station_depart_key = station_affichage_to_key[station_depart_affichage]
            # Recherche des nodes du graphe pour cette clé
            stations_nodes = [n for n, d in G.nodes(data=True) if d.get("station_key", "") == station_depart_key]
            if not stations_nodes:
                st.error(f"Station de départ « {station_depart_affichage} » (clé: {station_depart_key}) introuvable dans le réseau.")
                st.stop()
            # Recherche des stations proches du monument (toujours par clé)
            arr_candidates = find_stations_near_monument(
                monument_arrivee,
                rayon_m=900,
                monuments_csv=MONUMENTS_PATH,
                stations_csv=GRAPH_NODES_PATH
            )
            arr_station_keys = [st_key for st_key, _ in arr_candidates]
            if not arr_station_keys:
                st.error(f"Aucun accès métro/RER détecté pour le monument « {monument_arrivee} ».")
                st.stop()
            # Calcul du trajet (toujours avec la clé !)
            result = find_best_route(
                G=G,
                affluence_mapping=afflu_map,
                station_depart=station_depart_key,
                list_stations_arrivee=arr_station_keys,
                curseur=curseur,
                verbose=False
            )
            if result:
                st.success("Résultats trouvés !")
                for i, trajet in enumerate(result):
                    st.markdown(f"**Trajet #{i+1}**")
                    st.code(format_route(trajet))
            else:
                st.warning("Aucun trajet n'a pu être trouvé entre ces points pour vos critères.")
        except Exception as e:
            st.error(f"Erreur lors du calcul : {e}")

# --- Page 2 : À propos / future page custom ---
elif page == "À propos":
    st.title("À propos")
    st.markdown("""
    Projet Blob IA — Planificateur de trajets intelligent pour le métro/RER d'Île-de-France.  
    [Ajoute ici ta description, ton équipe, des liens, etc.]

    _Ajoute tes pages dans la sidebar pour enrichir l'application selon tes besoins !_
    """)

# ---- FIN ----
