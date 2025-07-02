import subprocess
import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def run_script(script_path):
    print(f"\n[PIPELINE] Exécution de : {script_path}")
    result = subprocess.run([sys.executable, script_path])
    if result.returncode != 0:
        print(f"[ERREUR] Le script {script_path} a échoué.")
        exit(1)
    print(f"[OK] {script_path} terminé.")

def main():
    # 1. Normalisation des données de gares
    run_script(os.path.join(BASE_DIR, "graph_builder", "normalize.py"))
    
    # 2. Construction du graphe (nodes/edges/graph_blobia.gpickle)
    run_script(os.path.join(BASE_DIR, "graph_builder", "build_graph.py"))
    
    # 3. Calcul des features d'affluence sur les stations
    run_script(os.path.join(BASE_DIR, "affluence_builder", "create_affluence.py"))
    
    # 4. (Optionnel) Ajoute ici d'autres étapes, ex: correspondances, enrichissement, QC...
    # run_script(os.path.join(BASE_DIR, "mon_script_en_plus.py"))
    
    print("\n[PIPELINE] Pipeline de données terminée ! Les fichiers dans ./data sont à jour.")

if __name__ == "__main__":
    main()
