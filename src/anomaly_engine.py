"""PhytoPulse - Detecteur d'anomalies NDVI + meteo (V1).

Lit l'historique NDVI et meteo, compare la periode courante a la normale,
et produit un anomaly_report.json avec statut, score et explication.

Ce module est une demonstration de data science explicable (regles + stats).
"""

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

NDVI_HISTORY_PATH = Path("data/ndvi_history_3ans.csv")
WEATHER_HISTORY_PATH = Path("data/weather_history_3ans.csv")
NDVI_CURRENT_PATH = Path("data/ndvi_timeseries.csv")
WEATHER_CURRENT_PATH = Path("data/weather_timeseries.csv")
OUTPUT_JSON_PATH = Path("data/anomaly_report.json")


def read_csv(path, required_columns):
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"Fichier vide ou sans en-tete : {path}")
        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Colonnes manquantes dans {path.name} : {', '.join(sorted(missing))}")
        for line_number, row in enumerate(reader, start=2):
            rows.append(row)
    return rows


def parse_date(s):
    return date.fromisoformat(s.strip())


def parse_float(s):
    if s is None or str(s).strip() == "":
        return None
    return float(s)


def read_ndvi_history():
    rows = read_csv(NDVI_HISTORY_PATH, {"date", "ndvi", "validpixelratio", "qualitystatus", "year"})
    data = []
    for row in rows:
        d = parse_date(row["date"])
        ndvi = parse_float(row["ndvi"])
        if ndvi is None:
            continue
        data.append({"date": d, "ndvi": ndvi, "year": int(row["year"])})
    return data


def read_weather_history():
    rows = read_csv(
        WEATHER_HISTORY_PATH,
        {"date", "tavg", "tmin", "tmax", "prcp", "et0"},
    )
    data = []
    for row in rows:
        d = parse_date(row["date"])
        tavg = parse_float(row["tavg"])
        prcp = parse_float(row["prcp"])
        et0 = parse_float(row["et0"])
        data.append(
            {
                "date": d,
                "tavg": tavg,
                "prcp": prcp,
                "et0": et0,
            }
        )
    return data


def read_current_ndvi():
    rows = read_csv(NDVI_CURRENT_PATH, {"date", "ndvi", "validpixelratio", "qualitystatus"})
    data = []
    for row in rows:
        d = parse_date(row["date"])
        ndvi = parse_float(row["ndvi"])
        if ndvi is None:
            continue
        data.append({"date": d, "ndvi": ndvi})
    return data


def read_current_weather():
    rows = read_csv(WEATHER_CURRENT_PATH, {"date", "temperature_2m_mean", "precipitation_sum", "et0_fao_evapotranspiration"})
    data = []
    for row in rows:
        d = parse_date(row["date"])
        tavg = parse_float(row["temperature_2m_mean"])
        prcp = parse_float(row["precipitation_sum"])
        et0 = parse_float(row["et0_fao_evapotranspiration"])
        data.append(
            {
                "date": d,
                "tavg": tavg,
                "prcp": prcp,
                "et0": et0,
            }
        )
    return data


def get_doy_window(d: date, window_days=30):
    """Retourne une liste de jours de l'année (doy) autour de d."""
    doys = []
    for delta in range(-window_days // 2, window_days // 2 + 1):
        dd = d + timedelta(days=delta)
        doys.append(dd.timetuple().tm_yday)
    return doys


def normal_ndvi_for_period(ndvi_history, current_data, window_days=30):
    """Calcule la normale NDVI (médiane) pour chaque date de current_data."""
    normals = {}
    for row in current_data:
        d = row["date"]
        doy = d.timetuple().tm_yday
        # Sélectionner les observations historiques dans une fenêtre autour de ce doy
        values = []
        for h in ndvi_history:
            h_doy = h["date"].timetuple().tm_yday
            # Fenêtre simple : +/- window_days/2 jours
            if abs(h_doy - doy) <= window_days // 2:
                values.append(h["ndvi"])
        if values:
            values_sorted = sorted(values)
            mid = len(values_sorted) // 2
            median = values_sorted[mid]
            normals[d] = median
    return normals


def anomaly_score_ndvi(current_ndvi, normal_ndvi):
    """Calcule un score d'anomalie NDVI (écart relatif à la normale)."""
    if normal_ndvi is None or normal_ndvi == 0:
        return 0.0
    return (current_ndvi - normal_ndvi) / normal_ndvi


def classify_anomaly(ndvi_anomaly_avg, water_deficit_days):
    """Classe l'anomalie en fonction du NDVI et du déficit hydrique."""
    if ndvi_anomaly_avg < -0.15 and water_deficit_days >= 10:
        return "anomalie_forte"
    if ndvi_anomaly_avg < -0.08 and water_deficit_days >= 5:
        return "anomalie_moderee"
    if ndvi_anomaly_avg < -0.05:
        return "anomalie_legere"
    return "pas_anomalie"


def build_report(ndvi_normals, current_ndvi, current_weather):
    # Calcul des anomalies NDVI
    ndvi_anomalies = []
    for row in current_ndvi:
        d = row["date"]
        ndvi = row["ndvi"]
        normal = ndvi_normals.get(d)
        if normal is None:
            continue
        anomaly = anomaly_score_ndvi(ndvi, normal)
        ndvi_anomalies.append({"date": d, "ndvi": ndvi, "normal": normal, "anomaly": anomaly})

    if not ndvi_anomalies:
        return {
            "analysis_type": "ndvi_meteo_anomaly_v1",
            "status": "donnees_insuffisantes",
            "confidence": "low",
            "explanation": ["Aucune comparaison NDVI actuelle vs normale n'a ete possible."],
        }

    # Anomalie NDVI moyenne
    anomaly_values = [x["anomaly"] for x in ndvi_anomalies]
    ndvi_anomaly_avg = sum(anomaly_values) / len(anomaly_values)

    # Déficit hydrique : jours où ET0 > prcp de manière marquée
    water_deficit_days = 0
    for row in current_weather:
        prcp = row["prcp"] or 0.0
        et0 = row["et0"] or 0.0
        if et0 > prcp + 1.0:  # seuil simple
            water_deficit_days += 1

    status = classify_anomaly(ndvi_anomaly_avg, water_deficit_days)

    explanation = [
        f"Sur la periode actuelle, le NDVI moyen est {ndvi_anomaly_avg*100:.1f}% par rapport a la normale historique.",
        f"{water_deficit_days} jour(s) presentent un deficit hydrique climatique marque (ET0 > precipitations).",
    ]

    if status.startswith("anomalie"):
        explanation.append(
            "Ces elements suggerent une anomalie NDVI+météo par rapport a l'historique, "
            "compatible avec un stress (hydrique ou autre), sans que cela puisse etre affirme avec certitude."
        )
    else:
        explanation.append(
            "Le NDVI actuel et le contexte meteo sont dans la continuite de l'historique, "
            "sans anomalie marquee detectee par ce modele simple."
        )

    confidence = "medium" if len(ndvi_anomalies) >= 3 else "low"

    return {
        "analysis_type": "ndvi_meteo_anomaly_v1",
        "status": status,
        "confidence": confidence,
        "metrics": {
            "ndvi_anomaly_mean": round(ndvi_anomaly_avg, 4),
            "water_deficit_days": water_deficit_days,
            "current_ndvi_count": len(current_ndvi),
            "normal_ndvi_count": len(ndvi_normals),
        },
        "explanation": explanation,
    }


def main():
    try:
        ndvi_history = read_ndvi_history()
        weather_history = read_weather_history()
        current_ndvi = read_current_ndvi()
        current_weather = read_current_weather()

        ndvi_normals = normal_ndvi_for_period(ndvi_history, current_ndvi, window_days=30)
        report = build_report(ndvi_normals, current_ndvi, current_weather)

        OUTPUT_JSON_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        print("\nPhytoPulse Anomaly Engine - V1")
        print("=" * 52)
        print(f"Statut      : {report['status']}")
        print(f"Confiance   : {report['confidence']}")
        print(f"Anomalie NDVI moyenne : {report['metrics']['ndvi_anomaly_mean']*100:.1f}%")
        print(f"Jours deficit hydrique : {report['metrics']['water_deficit_days']}")
        print(f"Rapport JSON cree : {OUTPUT_JSON_PATH}")

    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()