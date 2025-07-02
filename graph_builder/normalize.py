import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import correspondances_physiques_groupes
import pandas as pd
import unidecode

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def normalize_station_name(name):
    if name is None:
        return ""
    name = unidecode.unidecode(str(name))
    name = name.lower()
    name = name.replace("-", " ")
    name = name.replace("’", "'").replace("`", "'").replace("–", " ")
    name = " ".join(name.split())
    return name.strip()

def normalize_tables():
    stations_path = os.path.join(DATA_DIR, 'Stations_IDF.csv')
    gares_path = os.path.join(DATA_DIR, 'emplacement-des-gares-idf.csv')

    stations = pd.read_csv(stations_path)
    gares = pd.read_csv(gares_path)

    stations["station_norm"] = stations["station"].apply(normalize_station_name)
    gares["nom_so_gar_norm"] = gares["nom_so_gar"].apply(normalize_station_name)

    stations.to_csv(os.path.join(DATA_DIR, "Stations_IDF_normalized.csv"), index=False)
    gares.to_csv(os.path.join(DATA_DIR, "emplacement_des_gares_idf_normalized.csv"), index=False)
    print("Colonnes normalisées créées et fichiers sauvegardés.")

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

def align_tables_with_synonyms():
    synonym_mapping = build_synonym_mapping(correspondances_physiques_groupes, normalize_station_name)

    stations = pd.read_csv(os.path.join(DATA_DIR, "Stations_IDF_normalized.csv"))
    gares = pd.read_csv(os.path.join(DATA_DIR, "emplacement_des_gares_idf_normalized.csv"))

    stations["station_key"] = stations["station_norm"].apply(lambda n: map_to_master(n, synonym_mapping, lambda x: x))
    gares["gare_key"] = gares["nom_so_gar_norm"].apply(lambda n: map_to_master(n, synonym_mapping, lambda x: x))

    stations.to_csv(os.path.join(DATA_DIR, "Stations_IDF_aligned.csv"), index=False)
    gares.to_csv(os.path.join(DATA_DIR, "emplacement_des_gares_idf_aligned.csv"), index=False)

    n_aligned = (stations["station_norm"] != stations["station_key"]).sum()
    print(f"Mapping synonymes appliqué : {n_aligned} noms de stations alignés.")
    print("Colonnes 'station_key' et 'gare_key' créées et fichiers sauvegardés.")

if __name__ == "__main__":
    normalize_tables()
    align_tables_with_synonyms()
