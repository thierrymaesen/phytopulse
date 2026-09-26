"""Génère un historique NDVI synthétique 3 ans (2024-2026) pour PhytoPulse.

Ce fichier est une démonstration. Il ne représente pas des données réelles.
"""

import csv
import math
from datetime import date, timedelta
from pathlib import Path

OUTPUT_CSV = Path("data/ndvi_history_3ans.csv")

# Paramètres
START_DATE = date(2024, 4, 1)
END_DATE = date(2026, 9, 30)
INTERVAL_DAYS = 14  # tous les 14 jours

# Profil saisonnier de base (NDVI typique pour une culture/prairie en Belgique)
# pic vers jour 180 (fin juin / début juillet)
def seasonal_ndvi(d: date) -> float:
    doy = d.timetuple().tm_yday
    # pic à doy=180, valeur max ~0.75
    # min en hiver ~0.35
    amplitude = 0.40
    base = 0.55
    # fonction cosinus décalée
    ndvi = base + amplitude * math.cos((2 * math.pi / 365) * (doy - 180))
    return ndvi


def add_noise(value, noise_level=0.05):
    # bruit gaussien simple
    import random
    return value + random.gauss(0, noise_level)


def quality_status(ndvi, valid_ratio):
    if valid_ratio < 0.70:
        return "not_usable"
    if ndvi < 0.30:
        return "questionable"
    return "usable"


def main():
    rows = []
    current = START_DATE
    import random
    random.seed(42)  # reproductible

    while current <= END_DATE:
        year = current.year
        base_ndvi = seasonal_ndvi(current)

        # Ajout d'un stress en 2025 (été plus sec → NDVI plus bas)
        if year == 2025 and 180 <= current.timetuple().tm_yday <= 240:
            base_ndvi -= 0.12  # stress marqué

        ndvi = add_noise(base_ndvi, noise_level=0.04)
        ndvi = max(0.2, min(0.9, ndvi))  # bornes réalistes

        valid_ratio = 0.85 + random.gauss(0, 0.08)
        valid_ratio = max(0.5, min(1.0, valid_ratio))

        rows.append(
            {
                "date": current.isoformat(),
                "ndvi": round(ndvi, 4),
                "validpixelratio": round(valid_ratio, 2),
                "qualitystatus": quality_status(ndvi, valid_ratio),
                "year": year,
            }
        )

        current += timedelta(days=INTERVAL_DAYS)

    # Écriture CSV
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "ndvi", "validpixelratio", "qualitystatus", "year"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Historique NDVI généré : {OUTPUT_CSV}")
    print(f"Période : {START_DATE} -> {END_DATE}")
    print(f"Nombre d'observations : {len(rows)}")


if __name__ == "__main__":
    main()