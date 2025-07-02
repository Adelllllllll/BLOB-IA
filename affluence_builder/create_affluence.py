import sys
import os
import pandas as pd
import numpy as np

# Ajoute le dossier parent au PYTHONPATH pour importer utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import BIG_HUBS_SCORE, LINE_SCORE, DEFAULT_LINE_SCORE

# -- Fonctions utilitaires --
def normalize_station_key(name):
    import unidecode
    if name is None:
        return ""
    name = unidecode.unidecode(str(name))
    name = name.lower().replace("-", " ").replace("’", "'").replace("`", "'").replace("–", " ")
    name = " ".join(name.split())
    return name.strip()

def extract_main_line(ligne_str):
    s = str(ligne_str).strip().upper()
    parts = s.split()
    if len(parts) >= 2 and parts[0] in {"RER", "METRO"}:
        return f"{parts[0]} {parts[1]}"
    else:
        return s

# -- Chemins fichiers --
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'Stations_IDF_aligned.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'Stations_IDF_aligned_affluence.csv')

# -- Chargement du dataset --
df = pd.read_csv(DATA_PATH)
df["station_key"] = df["station_key"].astype(str).apply(normalize_station_key)
df["ligne"] = df["ligne"].astype(str)
df["main_line"] = df["ligne"].apply(extract_main_line)

# -- Colonne affluence_score vide --
df["affluence_score"] = np.nan

# 1. Affecte le score des BIG_HUBS sur toutes les lignes où ils apparaissent
for idx, row in df.iterrows():
    s_key = row["station_key"]
    score_hub = BIG_HUBS_SCORE.get(s_key, None)
    if score_hub is not None:
        df.at[idx, "affluence_score"] = score_hub  # score hub absolu, non pondéré

# 2. Bonus pour correspondances (multi-lignes) non hubs
corresp = df.groupby("station_key")["main_line"].nunique()
for s_key, n_lines in corresp[corresp > 1].items():
    if pd.isna(df.loc[df["station_key"] == s_key, "affluence_score"]).all():
        bonus = 0.5 + 0.05 * min(n_lines, 5)  # 0.5 à 0.75 max
        for idx in df[df["station_key"] == s_key].index:
            main_line = df.at[idx, "main_line"]
            line_score = LINE_SCORE.get(main_line, DEFAULT_LINE_SCORE)
            affluence = min(1.0, bonus * line_score)
            df.at[idx, "affluence_score"] = affluence

# 3. Propagation sur chaque branche réelle (ligne), pas juste main_line !
PROPAGATION_FACTOR = 0.9
SCORE_MIN = 0.15
for ligne, group in df.groupby("ligne"):
    indices = group.sort_values("ordre").index.tolist()
    # Sens croissant
    for i in range(1, len(indices)):
        if pd.isna(df.at[indices[i], "affluence_score"]) and not pd.isna(df.at[indices[i-1], "affluence_score"]):
            df.at[indices[i], "affluence_score"] = max(SCORE_MIN, df.at[indices[i-1], "affluence_score"] * PROPAGATION_FACTOR)
    # Sens décroissant
    for i in range(len(indices)-2, -1, -1):
        if pd.isna(df.at[indices[i], "affluence_score"]) and not pd.isna(df.at[indices[i+1], "affluence_score"]):
            df.at[indices[i], "affluence_score"] = max(SCORE_MIN, df.at[indices[i+1], "affluence_score"] * PROPAGATION_FACTOR)

# 4. Remplis les trous par le minimum
df["affluence_score"] = df["affluence_score"].fillna(SCORE_MIN)

# 5. Normalise max à 1.0 (au cas où)
df["affluence_score"] = df["affluence_score"].clip(upper=1.0)

# 6. Sauvegarde
df.to_csv(OUTPUT_PATH, index=False)
print(f"Fichier généré : {OUTPUT_PATH}")

# 7. Affiche quelques stats de vérif
print("\nDistribution des scores :")
print(df["affluence_score"].describe())
print("\nTop 15 stations les plus affluentes :")
print(df.sort_values("affluence_score", ascending=False)[["station_key", "main_line", "affluence_score"]].head(15))
