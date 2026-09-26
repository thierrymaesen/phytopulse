"""PhytoPulse - recuperation meteo historique pour le contexte NDVI.

Version compatible avec Meteostat 2.x. Elle utilise le point geographique
de field_config.json, recupere les series horaires d'une station proche,
les agrege en quotidien (tavg, tmin, tmax, prcp) puis calcule une ET0
estimee par Hargreaves-Samani.

La localisation ne represente pas necessairement la parcelle Sentinel-2.
Le script lit vegetation_change_report.json et archive les donnees dans
weather_timeseries.csv.
"""

import csv
import json
import math
import sys
from datetime import date
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

NDVI_REPORT_PATH = Path("data/vegetation_change_report.json")
OUTPUT_CSV = Path("data/weather_timeseries.csv")
FIELD_CONFIG_PATH = Path("field_config.json")

STATIONS_LIMIT = 4

# Meteostat : tavg/tmin/tmax en degres C, prcp en mm.
OUTPUT_COLUMNS = [
    "date",
    "temperature_2m_mean",
    "temperature_2m_min",
    "temperature_2m_max",
    "precipitation_sum",
    "et0_fao_evapotranspiration",
]


def read_field_config():
    if not FIELD_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Fichier de configuration de parcelle introuvable : {FIELD_CONFIG_PATH}. "
            "Assurez-vous que field_config.json est présent à la racine du projet."
        )
    config = json.loads(FIELD_CONFIG_PATH.read_text(encoding="utf-8"))
    for key in ("latitude", "longitude", "label"):
        if key not in config:
            raise ValueError(f"Clé requise manquante dans field_config.json : {key}")
    return config


FIELD_CONFIG = read_field_config()
LATITUDE = float(FIELD_CONFIG["latitude"])
LONGITUDE = float(FIELD_CONFIG["longitude"])
LOCATION_LABEL = FIELD_CONFIG["label"]


def read_ndvi_period(report_path):
    if not report_path.exists():
        raise FileNotFoundError(
            f"Rapport NDVI introuvable : {report_path}. Lancez d'abord vegetation_change_engine.py."
        )

    report = json.loads(report_path.read_text(encoding="utf-8"))
    period = report.get("period")
    if not period or not period.get("from") or not period.get("to"):
        raise ValueError("Le rapport NDVI ne contient pas de periode analysable.")

    return date.fromisoformat(period["from"]), date.fromisoformat(period["to"])


def value_or_empty(value):
    if value is None:
        return ""
    try:
        if value != value:  # NaN
            return ""
    except TypeError:
        pass
    return float(value)


def deg2rad(deg):
    return deg * math.pi / 180.0


def day_of_year(d: date) -> int:
    return d.timetuple().tm_yday


def extraterrestrial_radiation_MJ_per_m2_per_day(lat_deg: float, doy: int) -> float:
    """
    Calcule le rayonnement extraterrestre Ra (MJ/m²/jour) pour la latitude et le jour de l'année.
    Formule FAO-56, eq. 21.
    """
    lat = deg2rad(lat_deg)
    # Déclinaison solaire (rad)
    sol_dec = 0.409 * math.sin((2 * math.pi / 365) * doy - 1.39)
    # Distance relative Terre-Soleil
    ird = 1 + 0.033 * math.cos((2 * math.pi / 365) * doy)
    # Angle horaire au coucher du soleil (rad)
    sha_num = -math.tan(lat) * math.tan(sol_dec)
    # Protection contre les valeurs hors domaine pour acos
    sha_num = max(-1.0, min(1.0, sha_num))
    sha = math.acos(sha_num)

    # Rayonnement extraterrestre en MJ/m²/jour (FAO-56, eq. 21)
    Gsc = 0.0820  # MJ/m²/min
    Ra_MJ = (
        (24 * 60 / math.pi)
        * ird
        * (sha * math.sin(lat) * math.sin(sol_dec) + math.cos(lat) * math.cos(sol_dec) * math.sin(sha))
    )
    return Ra_MJ


def hargreaves_et0(tmin: float, tmax: float, tavg: float, Ra_MJ: float) -> float:
    """
    ET0 (mm/jour) par Hargreaves-Samani, version avec coefficient k_T.
    
    ET0 = 0.0023 * (tavg + 17.8) * sqrt(tmax - tmin) * (k_T * Ra)
    
    avec Ra en MJ/m²/jour et k_T = 0.035 (valeur typique pour estimation régionale).
    """
    k_T = 0.035  # coefficient empirique pour Rs ≈ k_T * Ra
    delta_t = tmax - tmin
    if delta_t <= 0:
        delta_t = 0.0
    Rs = k_T * Ra_MJ
    et0 = 0.0023 * (tavg + 17.8) * math.sqrt(delta_t) * Rs
    return max(0.0, et0)


def fetch_weather(start_date, end_date):
    point = ms.Point(LATITUDE, LONGITUDE)
    stations = ms.stations.nearby(point, limit=STATIONS_LIMIT)
    if stations.empty:
        raise RuntimeError("Meteostat n'a trouve aucune station proche du point provisoire.")

    # On récupère la première station via son index
    station_id = stations.index[0]
    station = ms.Station(station_id)

    # Récupération des données horaires
    hourly = ms.hourly(station, start_date, end_date).fetch()
    if hourly is None or hourly.empty:
        raise RuntimeError(
            "Meteostat n'a retourne aucune donnee horaire pour cette station et cette periode."
        )

    # Agrégation journalière : tavg, tmin, tmax, prcp
    daily_data = []
    for day_date in pd.date_range(start_date, end_date, freq="D"):
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
                }
            )
            continue

        temps = day_rows["temp"].dropna()
        prcp = day_rows["prcp"].sum() if "prcp" in day_rows.columns else None

        tavg = float(temps.mean()) if not temps.empty else None
        tmin = float(temps.min()) if not temps.empty else None
        tmax = float(temps.max()) if not temps.empty else None

        daily_data.append(
            {
                "date": day_date.date(),
                "tavg": tavg,
                "tmin": tmin,
                "tmax": tmax,
                "prcp": prcp,
            }
        )

    data = pd.DataFrame(daily_data).set_index("date")

    # Calcul ET0 journalier par Hargreaves-Samani
    et0_values = []
    for timestamp, row in data.iterrows():
        tmin = row.get("tmin")
        tmax = row.get("tmax")
        tavg = row.get("tavg")

        if tmin is None or tmax is None or tavg is None:
            et0_values.append(None)
            continue

        try:
            if math.isnan(tmin) or math.isnan(tmax) or math.isnan(tavg):
                et0_values.append(None)
                continue
        except TypeError:
            et0_values.append(None)
            continue

        doy = day_of_year(timestamp)
        Ra_MJ = extraterrestrial_radiation_MJ_per_m2_per_day(LATITUDE, doy)
        et0 = hargreaves_et0(float(tmin), float(tmax), float(tavg), Ra_MJ)
        et0_values.append(et0)

    data = data.copy()
    data["et0"] = et0_values

    return data, stations


def write_csv(data):
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()

        for timestamp, row in data.iterrows():
            et0 = row.get("et0")
            writer.writerow(
                {
                    "date": timestamp.isoformat(),
                    "temperature_2m_mean": value_or_empty(row.get("tavg")),
                    "temperature_2m_min": value_or_empty(row.get("tmin")),
                    "temperature_2m_max": value_or_empty(row.get("tmax")),
                    "precipitation_sum": value_or_empty(row.get("prcp")),
                    "et0_fao_evapotranspiration": value_or_empty(et0),
                }
            )


def format_station_ids(stations):
    if stations is None or "id" not in stations.columns:
        return "non disponibles"
    return ", ".join(str(value) for value in stations["id"].tolist())


def main():
    try:
        start_date, end_date = read_ndvi_period(NDVI_REPORT_PATH)
        data, stations = fetch_weather(start_date, end_date)
        write_csv(data)

        print("\nPhytoPulse Weather Fetcher - V1")
        print("=" * 52)
        print(f"Localisation : {LOCATION_LABEL}")
        print(f"Coordonnees  : {LATITUDE:.4f}, {LONGITUDE:.4f}")
        print(f"Periode      : {start_date.isoformat()} -> {end_date.isoformat()}")
        print("Source       : Meteostat Hourly, agrege en quotidien")
        print(
            f"Stations     : {format_station_ids(stations)}"
        )
        print(f"Jours recues : {len(data)}")
        print(f"Fichier cree : {OUTPUT_CSV}")
        print("ET0          : calculee par Hargreaves-Samani a partir de tmin/tmax/tavg.")
        print("Limite       : contexte meteo regional/provisoire, pas meteo mesuree sur la parcelle.")
    except (FileNotFoundError, ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()