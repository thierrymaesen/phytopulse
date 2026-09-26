"""PhytoPulse - moteur explicable de contexte meteo (V1).

Lit weather_timeseries.csv, vegetation_change_report.json et field_config.json,
puis produit un weather_context_report.json local. Le moteur decrit des
cooccurrences entre meteo et signal NDVI ; il n'attribue pas de causalite agronomique.
"""

import csv
import json
import sys
from pathlib import Path

NDVI_REPORT_PATH = Path("data/vegetation_change_report.json")
WEATHER_CSV_PATH = Path("data/weather_timeseries.csv")
OUTPUT_JSON_PATH = Path("data/weather_context_report.json")
FIELD_CONFIG_PATH = Path("field_config.json")

DRY_DAY_PRECIPITATION_MM = 1.0
DRY_PERIOD_SHARE = 0.70
LOW_RAINFALL_MM_PER_DAY = 1.0
WARM_MEAN_TEMPERATURE_C = 20.0

REQUIRED_COLUMNS = {
    "date",
    "temperature_2m_mean",
    "temperature_2m_min",
    "temperature_2m_max",
    "precipitation_sum",
    "et0_fao_evapotranspiration",
}


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

LOCATION = {
    "label": FIELD_CONFIG["label"],
    "latitude": float(FIELD_CONFIG["latitude"]),
    "longitude": float(FIELD_CONFIG["longitude"]),
    "precision_note": (
        "La localisation provient de field_config.json ; "
        "elle ne correspond pas necessairement a la parcelle NDVI."
    ),
}


def number_or_none(value):
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def read_ndvi_report():
    if not NDVI_REPORT_PATH.exists():
        raise FileNotFoundError(
            f"Rapport NDVI introuvable : {NDVI_REPORT_PATH}. Lancez vegetation_change_engine.py."
        )
    report = json.loads(NDVI_REPORT_PATH.read_text(encoding="utf-8"))
    period = report.get("period")
    if not period or not period.get("from") or not period.get("to"):
        raise ValueError("Le rapport NDVI ne contient pas de periode analysable.")
    return report


def read_weather_rows():
    if not WEATHER_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Fichier meteo introuvable : {WEATHER_CSV_PATH}. Lancez weather_fetcher.py."
        )

    rows = []
    with WEATHER_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Le fichier meteo est vide ou sans en-tete.")
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError("Colonnes meteo manquantes : " + ", ".join(sorted(missing)))

        for line_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    {
                        "date": row["date"].strip(),
                        "temperature_2m_mean": number_or_none(row["temperature_2m_mean"]),
                        "temperature_2m_min": number_or_none(row["temperature_2m_min"]),
                        "temperature_2m_max": number_or_none(row["temperature_2m_max"]),
                        "precipitation_sum": number_or_none(row["precipitation_sum"]),
                        "et0_fao_evapotranspiration": number_or_none(row["et0_fao_evapotranspiration"]),
                    }
                )
            except ValueError as exc:
                raise ValueError(f"Ligne meteo invalide {line_number} : {exc}") from exc
    return rows


def mean(values):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else None


def minimum(values):
    values = [value for value in values if value is not None]
    return min(values) if values else None


def maximum(values):
    values = [value for value in values if value is not None]
    return max(values) if values else None


def round_or_none(value, digits=2):
    return round(value, digits) if value is not None else None


def classify_weather(days, dry_days, rainfall_total, mean_temp, et0_total):
    dry_share = dry_days / days if days else 0
    rainfall_per_day = rainfall_total / days if days else 0

    if dry_share >= DRY_PERIOD_SHARE and rainfall_per_day < LOW_RAINFALL_MM_PER_DAY:
        if mean_temp is not None and mean_temp >= WARM_MEAN_TEMPERATURE_C:
            return "periode_chaude_et_majoritairement_seche"
        return "periode_majoritairement_seche"

    if et0_total is not None and et0_total > rainfall_total:
        return "demande_evaporative_superieure_aux_precipitations"

    return "conditions_meteo_sans_signal_simple"


def build_report(ndvi_report, weather_rows):
    period = ndvi_report["period"]
    start_date, end_date = period["from"], period["to"]
    rows = [row for row in weather_rows if start_date <= row["date"] <= end_date]

    base = {
        "analysis_type": "explainable_weather_context_v1",
        "model_type": "rule_based_not_trained_ml",
        "source": "Meteostat Daily via weather_timeseries.csv",
        "location": LOCATION,
        "period": {"from": start_date, "to": end_date, "ndvi_period_days": period["days"]},
        "thresholds": {
            "dry_day_precipitation_mm": DRY_DAY_PRECIPITATION_MM,
            "dry_period_share": DRY_PERIOD_SHARE,
            "low_rainfall_mm_per_day": LOW_RAINFALL_MM_PER_DAY,
            "warm_mean_temperature_c": WARM_MEAN_TEMPERATURE_C,
        },
        "limitations": [
            LOCATION["precision_note"],
            "Les donnees Meteostat sont derivees de stations proches et d'une interpolation vers ce point.",
            "L'ET0 est une estimation Hargreaves-Samani, calculee a partir des temperatures Meteostat et du rayonnement extraterrestre theorique.",
            "La meteo et le NDVI peuvent etre correles sans relation de causalite directe.",
            "L'irrigation, le type de culture, le stade phenologique, le sol et les pratiques agricoles ne sont pas connus ici.",
            "Ce rapport est un contexte descriptif et non un diagnostic agronomique.",
        ],
    }

    if not rows:
        return {
            **base,
            "status": "donnees_meteo_insuffisantes",
            "confidence": "insufficient",
            "weather_days_count": 0,
            "explanation": ["Aucune observation meteo ne couvre la periode NDVI analysee."],
        }

    precipitation = [row["precipitation_sum"] for row in rows]
    temperatures = [row["temperature_2m_mean"] for row in rows]
    min_temperatures = [row["temperature_2m_min"] for row in rows]
    max_temperatures = [row["temperature_2m_max"] for row in rows]
    et0_values = [row["et0_fao_evapotranspiration"] for row in rows]

    valid_precipitation = [value for value in precipitation if value is not None]
    rainfall_total = sum(valid_precipitation)
    et0_total = sum(value for value in et0_values if value is not None) if any(value is not None for value in et0_values) else None
    dry_days = sum(value < DRY_DAY_PRECIPITATION_MM for value in valid_precipitation)
    weather_days_count = len(rows)
    dry_share = dry_days / len(valid_precipitation) if valid_precipitation else 0
    mean_temp = mean(temperatures)
    status = classify_weather(weather_days_count, dry_days, rainfall_total, mean_temp, et0_total)

    ndvi_status = ndvi_report.get("status", "inconnu")
    temperature_coverage = sum(value is not None for value in temperatures)
    explanation = [
        f"{weather_days_count} jour(s) meteorologiques couvrent la periode NDVI du {start_date} au {end_date}.",
        f"Le cumul de precipitation est de {rainfall_total:.1f} mm, avec {dry_days} jour(s) sous {DRY_DAY_PRECIPITATION_MM:.1f} mm.",
    ]
    if mean_temp is not None:
        explanation.append(f"La temperature moyenne est de {mean_temp:.1f} °C.")
    else:
        explanation.append(
            "Les temperatures journalières ne sont pas disponibles pour cette extraction Meteostat ; "
            "le statut repose uniquement sur les precipitations."
        )
    if et0_total is not None:
        explanation.append(
            f"L'evapotranspiration de reference estimee par Hargreaves-Samani est de {et0_total:.1f} mm."
        )
    else:
        explanation.append("L'evapotranspiration de reference ET0 n'est pas disponible faute de temperatures Meteostat exploitables.")
    if ndvi_status.startswith("baisse"):
        explanation.append(
            "La baisse du NDVI et ce contexte meteo sont temporellement associes ; "
            "cela ne permet pas de conclure a une cause meteorologique."
        )
    else:
        explanation.append(
            "Le contexte meteo est decrit pour la meme periode que le NDVI ; "
            "il ne permet pas d'attribuer une cause au signal de vegetation."
        )

    confidence = "medium" if valid_precipitation else "low"
    return {
        **base,
        "status": status,
        "confidence": confidence,
        "weather_days_count": weather_days_count,
        "data_coverage": {
            "precipitation_days": len(valid_precipitation),
            "temperature_mean_days": temperature_coverage,
            "et0_days": sum(value is not None for value in et0_values),
        },
        "metrics": {
            "precipitation_total_mm": round_or_none(rainfall_total),
            "precipitation_daily_mean_mm": round_or_none(rainfall_total / weather_days_count),
            "dry_days_count": dry_days,
            "dry_days_share": round_or_none(dry_share, 3),
            "temperature_mean_c": round_or_none(mean_temp),
            "temperature_min_c": round_or_none(minimum(min_temperatures)),
            "temperature_max_c": round_or_none(maximum(max_temperatures)),
            "et0_total_mm": round_or_none(et0_total),
            "water_balance_proxy_mm": round_or_none(rainfall_total - et0_total) if et0_total is not None else None,
        },
        "explanation": explanation,
    }


def format_optional_metric(value, unit):
    return f"{value:.1f} {unit}" if value is not None else f"non disponible ({unit})"


def print_summary(report):
    print("\nPhytoPulse Weather Context - V1")
    print("=" * 52)
    print(f"Statut      : {report['status']}")
    print(f"Confiance   : {report['confidence']}")
    print(f"Localisation: {report['location']['label']}")

    metrics = report.get("metrics")
    if not metrics:
        print("Analyse     : impossible faute de donnees meteo pour la periode NDVI.")
        return

    print(f"Precip.     : {format_optional_metric(metrics['precipitation_total_mm'], 'mm')}")
    print(f"Jours secs  : {metrics['dry_days_count']}/{report['weather_days_count']}")
    print(f"Temp. moy.  : {format_optional_metric(metrics['temperature_mean_c'], '°C')}")
    if metrics["et0_total_mm"] is not None:
        print(f"ET0         : {format_optional_metric(metrics['et0_total_mm'], 'mm')} (estimation Hargreaves-Samani)")
        print(f"Bilan proxy : {format_optional_metric(metrics['water_balance_proxy_mm'], 'mm')} (precipitations - ET0)")
    else:
        print("ET0         : non disponible faute de temperatures Meteostat exploitables.")
    print("Limite      : cooccurrence meteo/NDVI, pas causalite demontree.")


def main():
    try:
        ndvi_report = read_ndvi_report()
        weather_rows = read_weather_rows()
        report = build_report(ndvi_report, weather_rows)
        OUTPUT_JSON_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print_summary(report)
        print(f"\nRapport JSON cree : {OUTPUT_JSON_PATH}")
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()