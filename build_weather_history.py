"""Génère un historique météo 3 ans (2024-2026) via Meteostat pour PhytoPulse.

Ce fichier est une démonstration. Il utilise les coordonnées de field_config.json.
"""

import csv
import json
import math
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

try:
    import meteostat as ms
except ImportError:
    print(
        "Erreur : Meteostat n'est pas installe. Executez : py -m pip install meteostat",
        file=sys.stderr,
    )
    sys.exit(1)

FIELD_CONFIG_PATH = Path("field_config.json")
OUTPUT_CSV = Path("data/weather_history_3ans.csv")

START_DATE = date(2024, 4, 1)
END_DATE = date(2026, 9, 30)
STATIONS_LIMIT = 4


def read_field_config():
    if not FIELD_CONFIG_PATH.exists():
        raise FileNotFoundError(f"Fichier de configuration introuvable : {FIELD_CONFIG_PATH}")
    config = json.loads(FIELD_CONFIG_PATH.read_text(encoding="utf-8"))
    for key in ("latitude", "longitude", "label"):
        if key not in config:
            raise ValueError(f"Clé requise manquante dans field_config.json : {key}")
    return config


FIELD_CONFIG = read_field_config()
LATITUDE = float(FIELD_CONFIG["latitude"])
LONGITUDE = float(FIELD_CONFIG["longitude"])


def deg2rad(deg):
    return deg * math.pi / 180.0


def day_of_year(d: date) -> int:
    return d.timetuple().tm_yday


def extraterrestrial_radiation_MJ_per_m2_per_day(lat_deg: float, doy: int) -> float:
    lat = deg2rad(lat_deg)
    sol_dec = 0.409 * math.sin((2 * math.pi / 365) * doy - 1.39)
    ird = 1 + 0.033 * math.cos((2 * math.pi / 365) * doy)
    sha_num = -math.tan(lat) * math.tan(sol_dec)
    sha_num = max(-1.0, min(1.0, sha_num))
    sha = math.acos(sha_num)

    Gsc = 0.0820  # MJ/m²/min
    Ra_MJ = (
        (24 * 60 / math.pi)
        * ird
        * (sha * math.sin(lat) * math.sin(sol_dec) + math.cos(lat) * math.cos(sol_dec) * math.sin(sha))
    )
    return Ra_MJ


def hargreaves_et0(tmin: float, tmax: float, tavg: float, Ra_MJ: float) -> float:
    k_T = 0.035
    delta_t = tmax - tmin
    if delta_t <= 0:
        delta_t = 0.0
    Rs = k_T * Ra_MJ
    et0 = 0.0023 * (tavg + 17.8) * math.sqrt(delta_t) * Rs
    return max(0.0, et0)


def main():
    point = ms.Point(LATITUDE, LONGITUDE)
    stations = ms.stations.nearby(point, limit=STATIONS_LIMIT)
    if stations.empty:
        raise RuntimeError("Meteostat n'a trouve aucune station proche.")

    station_id = stations.index[0]
    station = ms.Station(station_id)

    # Récupération hourly sur toute la période
    hourly = ms.hourly(station, START_DATE, END_DATE).fetch()
    if hourly is None or hourly.empty:
        raise RuntimeError("Meteostat n'a retourne aucune donnee horaire.")

    # Agrégation journalière
    daily_data = []
    for day_date in pd.date_range(START_DATE, END_DATE, freq="D"):
        day_start = pd.Timestamp(day_date.date())
        day_end = day_start + pd.Timedelta(days=1)

        mask = (hourly.index >= day_start) & (hourly.index < day_end)
        day_rows = hourly.loc[mask]

        if day_rows.empty:
            daily_data.append(
                {
                    "date": day_date.date(),
                    "tavg": None,
                    "tmin": None,
                    "tmax": None,
                    "prcp": None,
                    "et0": None,
                }
            )
            continue

        temps = day_rows["temp"].dropna()
        prcp = day_rows["prcp"].sum() if "prcp" in day_rows.columns else None

        tavg = float(temps.mean()) if not temps.empty else None
        tmin = float(temps.min()) if not temps.empty else None
        tmax = float(temps.max()) if not temps.empty else None

        # Calcul ET0
        et0 = None
        if tmin is not None and tmax is not None and tavg is not None:
            try:
                if not (math.isnan(tmin) or math.isnan(tmax) or math.isnan(tavg)):
                    doy = day_of_year(day_date.date())
                    Ra_MJ = extraterrestrial_radiation_MJ_per_m2_per_day(LATITUDE, doy)
                    et0 = hargreaves_et0(tmin, tmax, tavg, Ra_MJ)
            except Exception:
                et0 = None

        daily_data.append(
            {
                "date": day_date.date(),
                "tavg": tavg,
                "tmin": tmin,
                "tmax": tmax,
                "prcp": prcp,
                "et0": et0,
            }
        )

    data = pd.DataFrame(daily_data).set_index("date")

    # Écriture CSV
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "tavg", "tmin", "tmax", "prcp", "et0"])
        writer.writeheader()
        for timestamp, row in data.iterrows():
            writer.writerow(
                {
                    "date": timestamp.isoformat(),
                    "tavg": row["tavg"] if row["tavg"] is not None else "",
                    "tmin": row["tmin"] if row["tmin"] is not None else "",
                    "tmax": row["tmax"] if row["tmax"] is not None else "",
                    "prcp": row["prcp"] if row["prcp"] is not None else "",
                    "et0": row["et0"] if row["et0"] is not None else "",
                }
            )

    print(f"Historique météo généré : {OUTPUT_CSV}")
    print(f"Période : {START_DATE} -> {END_DATE}")
    print(f"Nombre de jours : {len(data)}")


if __name__ == "__main__":
    main()