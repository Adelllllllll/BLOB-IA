import pandas as pd
from geopy.distance import geodesic
import unidecode

def normalize_name(name):
    if not isinstance(name, str):
        return ""
    name = unidecode.unidecode(name).lower().replace("-", " ")
    name = name.replace("’", "'").replace("`", "'").replace("–", " ")
    return " ".join(name.split()).strip()

def find_stations_near_monument(
        monument_name,
        rayon_m=900,
        monuments_csv="data/monuments.csv",
        stations_csv="data/graph_nodes.csv"
    ):
    # Charger monuments (attention aux noms de colonnes !)
    monuments = pd.read_csv(monuments_csv, encoding='cp1252')
    monuments["monument_norm"] = monuments["Monument"].apply(normalize_name)
    monument_norm = normalize_name(monument_name)
    row = monuments[monuments["monument_norm"] == monument_norm]
    if row.empty:
        raise ValueError(f"Monument '{monument_name}' non trouvé dans {monuments_csv}")
    lat_m, lon_m = float(row.iloc[0]["Latitude"]), float(row.iloc[0]["Longitude"])

    # Charger stations
    stations = pd.read_csv(stations_csv)
    stations["station_key"] = stations["gare_key"].apply(normalize_name)
    stations = stations.drop_duplicates("station_key")
    stations = stations.dropna(subset=["latitude", "longitude"])

    results = []
    for _, row in stations.iterrows():
        lat_s, lon_s = float(row["latitude"]), float(row["longitude"])
        dist = geodesic((lat_m, lon_m), (lat_s, lon_s)).meters
        if dist <= rayon_m:
            results.append((row["station_key"], dist))
    if not results:
        stations["distance"] = stations.apply(
            lambda r: geodesic((lat_m, lon_m), (float(r["latitude"]), float(r["longitude"]))).meters, axis=1)
        min_row = stations.loc[stations["distance"].idxmin()]
        return [(min_row["station_key"], min_row["distance"])]
    results = sorted(results, key=lambda x: x[1])
    return results

if __name__ == "__main__":
    stations = find_stations_near_monument("Tour Eiffel", rayon_m=600)
    print("Stations proches :", stations)
