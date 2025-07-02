import os
import pandas as pd
import sys

# Importe les profils jour/heure directement depuis utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import PROFILE_JOUR, PROFILE_HEURE

SCORE_MIN = 0.15

def get_affluence_mapping(affluence_df, jour, heure):
    """
    Retourne { (station_key, ligne): affluence_dynamique } pour le jour/heure demandés.
    """
    coef_jour = PROFILE_JOUR.get(jour.lower(), 0.7)
    coef_heure = PROFILE_HEURE.get(int(heure), 0.5)
    mapping = {}
    for _, row in affluence_df.iterrows():
        score = min(1.0, row['affluence_score'] * coef_jour * coef_heure)
        mapping[(row['station_key'], row['ligne'])] = score
    return mapping

def get_affluence_mapping_from_file(affluence_path, jour, heure):
    """
    Version qui lit directement le CSV. (Facultatif)
    """
    df = pd.read_csv(affluence_path)
    df["station_key"] = df["station_key"].astype(str).str.strip().str.lower()
    df["ligne"] = df["ligne"].astype(str).str.strip()
    return get_affluence_mapping(df, jour, heure)

def apply_affluence_to_graph(G, affluence_mapping):
    """
    Applique les scores dynamiques à chaque noeud du graphe NetworkX.
    """
    for node, data in G.nodes(data=True):
        skey = data.get('station_key')
        ligne = data.get('ligne')
        score = affluence_mapping.get((skey, ligne), SCORE_MIN)
        G.nodes[node]['affluence_dynamique'] = score
    return G

# Optionnel : Si besoin de test rapide
if __name__ == "__main__":
    affluence_path = "data/Stations_IDF_aligned_affluence.csv"
    mapping = get_affluence_mapping_from_file(affluence_path, "lundi", 8)
    print("Exemple de scores dynamiques (top 10) :")
    for k, v in list(mapping.items())[:10]:
        print(k, v)
    # Trie le mapping par valeur décroissante
    top10 = sorted(mapping.items(), key=lambda x: -x[1])[:10]
    print("TOP 10 stations par affluence dynamique :")
    for (station_key, ligne), score in top10:
        print(f"{station_key:35s} {ligne:10s} {score:.4f}")

