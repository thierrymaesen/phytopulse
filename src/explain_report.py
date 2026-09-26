"""PhytoPulse - Génération d'une explication lisible des rapports."""

import json
import sys
from pathlib import Path

VEG_REPORT_PATH = Path("data/vegetation_change_report.json")
WEATHER_REPORT_PATH = Path("data/weather_context_report.json")
ANOMALY_REPORT_PATH = Path("data/anomaly_report.json")
OUTPUT_JSON_PATH = Path("data/explain_report.json")

STATUS_LABELS = {
    "baisse_moderee_a_examiner": "baisse modérée à examiner",
    "periode_chaude_et_majoritairement_seche": "période chaude et majoritairement sèche",
    "anomalie_forte": "anomalie forte",
    "anomalie_moderee": "anomalie modérée",
    "anomalie_legere": "anomalie légère",
    "pas_anomalie": "pas d’anomalie",
    "donnees_insuffisantes": "données insuffisantes",
}


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def humanize_status(value):
    if not value:
        return "inconnu"
    return STATUS_LABELS.get(value, str(value).replace("_", " "))


def first_value(mapping, *keys):
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def build_explanation(veg, weather, anomaly):
    paragraphs = [
        "Ce rapport synthétise l'état de la parcelle sur la période récente, "
        "en combinant évolution NDVI, contexte météo et détection d'anomalies."
    ]

    if veg and veg.get("status") != "donnees_insuffisantes":
        ndvi = veg.get("ndvi", {})
        ndvi_start = ndvi.get("from")
        ndvi_end = ndvi.get("to")
        delta = ndvi.get("delta")
        status = humanize_status(veg.get("status"))

        if ndvi_start is not None and ndvi_end is not None and delta is not None:
            paragraphs.append(
                f"Sur la période analysée, le NDVI est passé de {ndvi_start:.4f} à {ndvi_end:.4f}, "
                f"soit une variation de {delta:+.4f}. Le statut du changement est : {status}. "
                "Cela indique un signal de changement de végétation, sans que la cause puisse être affirmée avec certitude."
            )
        else:
            paragraphs.append(
                f"Un changement de végétation a été détecté (statut : {status}), "
                "mais les métriques détaillées ne sont pas disponibles."
            )
    else:
        paragraphs.append(
            "Les données NDVI actuelles sont insuffisantes pour caractériser un changement de végétation."
        )

    if weather and weather.get("status") != "donnees_insuffisantes":
        metrics = weather.get("metrics", {})
        status = humanize_status(weather.get("status"))
        prcp = first_value(metrics, "precipitation_sum_mm", "precipitation_total_mm", "precip_mm")
        dry_days = first_value(metrics, "dry_days_count", "dry_days")
        tavg = first_value(metrics, "temperature_mean_c", "temperature_avg_c", "mean_temperature_c")
        et0 = first_value(metrics, "et0_sum_mm", "et0_total_mm", "et0_mm")

        if all(value is not None for value in (prcp, dry_days, tavg, et0)):
            paragraphs.append(
                f"Le contexte météo sur la même période est décrit comme : {status}. "
                f"La précipitation totale est de {prcp:.1f} mm, avec {dry_days} jour(s) sec(s). "
                f"La température moyenne est de {tavg:.1f} °C et l'ET0 cumulée est de {et0:.1f} mm. "
                "Ces conditions sont compatibles avec un stress hydrique potentiel, sans que cela soit directement mesuré sur la parcelle."
            )
        else:
            paragraphs.append(
                f"Le contexte météo est décrit comme : {status}, "
                "mais les métriques détaillées ne sont pas disponibles."
            )
    else:
        paragraphs.append(
            "Le contexte météo n'a pas pu être analysé de manière fiable sur cette période."
        )

    if anomaly and anomaly.get("status") not in (None, "donnees_insuffisantes"):
        status = humanize_status(anomaly.get("status"))
        confidence = anomaly.get("confidence", "inconnue")
        metrics = anomaly.get("metrics", {})
        ndvi_anomaly = metrics.get("ndvi_anomaly_mean", 0) * 100
        deficit_days = metrics.get("water_deficit_days", 0)
        paragraphs.append(
            f"L'analyse d'anomalie NDVI+météo indique un statut : {status} "
            f"(confiance {confidence}). Le NDVI moyen s'écarte de {ndvi_anomaly:+.1f}% "
            f"par rapport à la normale historique, et {deficit_days} jour(s) présentent un déficit hydrique climatique marqué. "
            "Cela renforce l'hypothèse d'un stress (hydrique ou autre), sans preuve directe de causalité."
        )
    else:
        paragraphs.append(
            "L'analyse d'anomalie NDVI+météo n'a pas pu être réalisée de manière fiable."
        )

    paragraphs.append(
        "Ces interprétations reposent sur des données satellitaires et météorologiques régionales, "
        "et doivent être combinées avec une observation terrain pour un diagnostic complet."
    )

    return {
        "report_type": "explain_report_v3",
        "explanation_paragraphs": paragraphs,
        "explanation_text": "\n\n".join(paragraphs),
    }


def main():
    try:
        report = build_explanation(
            load_json(VEG_REPORT_PATH),
            load_json(WEATHER_REPORT_PATH),
            load_json(ANOMALY_REPORT_PATH),
        )
        OUTPUT_JSON_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("\nPhytoPulse Explain Report - V3")
        print("=" * 52)
        print("Rapport d'explication genere : data\\explain_report.json")
        print("\nExtrait de l'explication :")
        print("-" * 52)
        print("\n".join(report["explanation_paragraphs"][:2]))
        print("-" * 52)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
