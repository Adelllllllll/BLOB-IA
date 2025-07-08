import sys
import os
import pandas as pd
import unidecode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import correspondances_physiques_groupes

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def normalize_station_name(name):
    if pd.isnull(name):
        return ""
    name = unidecode.unidecode(str(name))
    name = name.lower()
    name = name.replace("-", " ")
    name = name.replace("’", "'").replace("`", "'").replace("–", " ")
    name = " ".join(name.split())
    return name.strip()

def build_synonym_mapping(correspondance_groupes, normalizer):
    mapping = {}
    for groupe in correspondance_groupes:
        if not groupe:
            continue
        master = normalizer(groupe[0])
        for alias in groupe:
            mapping[normalizer(alias)] = master
    return mapping

def map_to_master(name, mapping, normalizer):
    norm = normalizer(name)
    return mapping.get(norm, norm)

if __name__ == "__main__":
    stations = pd.read_csv(os.path.join(DATA_DIR, "Stations_IDF.csv"))
    gares = pd.read_csv(os.path.join(DATA_DIR, "emplacement-des-gares-idf.csv"))

    # Normalisation pour jointure temporaire
    stations["station_norm"] = stations["station"].apply(normalize_station_name)
    gares["nom_so_gar_norm"] = gares["nom_so_gar"].apply(normalize_station_name)

    synonym_mapping = build_synonym_mapping(correspondances_physiques_groupes, normalize_station_name)
    stations["station_key"] = stations["station_norm"].apply(lambda n: map_to_master(n, synonym_mapping, lambda x: x))
    gares["gare_key"] = gares["nom_so_gar_norm"].apply(lambda n: map_to_master(n, synonym_mapping, lambda x: x))

    # On prend latitude/longitude des colonnes correspondantes
    gares['latitude'] = pd.to_numeric(gares['Geo Point'], errors='coerce')
    gares['longitude'] = pd.to_numeric(gares['Geo Shape'], errors='coerce')

    # Jointure sur la clé
    merged = stations.merge(
        gares[['gare_key', 'latitude', 'longitude']],
        left_on='station_key',
        right_on='gare_key',
        how='left'
    )

    # Suppression des colonnes internes de normalisation
    merged = merged.drop(columns=['station_norm', 'station_key', 'gare_key'], errors='ignore')

    output_path = os.path.join(DATA_DIR, "Stations_IDF_fusion_GPS.csv")
    merged.to_csv(output_path, index=False)
    n_with_coords = merged[["latitude", "longitude"]].dropna().shape[0]

    print(f"✅ Fusion terminée ! Fichier créé : {output_path}")
    print(f"{n_with_coords} stations disposent de coordonnées GPS.")
    print(f"Colonnes du dataset final : {list(merged.columns)}")
