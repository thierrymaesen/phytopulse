"""PhytoPulse - Script principal du pipeline (V2).

Orchestre les etapes :
1. vegetation_change_engine.py
2. weather_fetcher.py
3. weather_context_engine.py
4. anomaly_engine.py
5. explain_report.py

Usage :
    py .\run_phytopulse.py
"""

import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SCRIPTS = [
    "vegetation_change_engine.py",
    "weather_fetcher.py",
    "weather_context_engine.py",
    "anomaly_engine.py",
    "explain_report.py",
]


def run_script(script_name):
    script_path = PROJECT_DIR / "src" / script_name
    if not script_path.exists():
        print(f"Avertissement : {script_name} introuvable, ignore.")
        return True
    print(f"\nExecution de {script_name}...")
    result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_DIR)
    if result.returncode != 0:
        print(f"Echec : {script_name}")
        return False
    print(f"Succes : {script_name} termine.")
    return True


def main():
    print("PhytoPulse Pipeline - V2")
    print("=" * 52)
    print(f"Dossier projet : {PROJECT_DIR}")

    for script in SCRIPTS:
        ok = run_script(script)
        if not ok:
            print("\nPipeline interrompu (erreur dans un script).")
            sys.exit(1)

    print("\n" + "=" * 52)
    print("Pipeline termine avec succes.")
    print("Rapports mis a jour :")
    print("- data\\vegetation_change_report.json")
    print("- data\\weather_context_report.json")
    print("- data\\anomaly_report.json")
    print("- data\\explain_report.json")
    print("\nActualisez ensuite le dashboard avec Ctrl + F5.")


if __name__ == "__main__":
    main()