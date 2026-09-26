"""PhytoPulse - moteur explicable de changement NDVI (V1).

Lit le fichier local ndvi_timeseries.csv, compare les deux dernieres
observations exploitables et produit un rapport JSON. Ce module ne contacte
aucune API, ne lit aucun secret et ne modifie pas le CSV source.

Limite importante : il s'agit d'une aide a l'interpretation basee sur des
regles explicites, pas d'un diagnostic agronomique ni d'un modele ML entraine.
"""

import csv
import json
import sys
from datetime import date
from pathlib import Path

INPUT_CSV = Path("data/ndvi_timeseries.csv")
OUTPUT_JSON_PATH = Path("data/vegetation_change_report.json")

# Seuils exprimes en PROPORTION (0.0 a 1.0), car le CSV utilise 0.99 = 99 %
MIN_VALID_PIXELS_RATIO = 0.70
HIGH_CONFIDENCE_PIXELS_RATIO = 0.90

STABLE_DELTA_NDVI = 0.02
IMPORTANT_DELTA_NDVI = 0.05

REQUIRED_COLUMNS = {"date", "ndvi", "validpixelratio", "qualitystatus"}


def read_observations(csv_path):
    if not csv_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {csv_path}")

    observations = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Le fichier CSV est vide ou ne contient pas d'en-tete.")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError("Colonnes manquantes : " + ", ".join(sorted(missing)))

        for line_number, row in enumerate(reader, start=2):
            try:
                observations.append(
                    {
                        "date": date.fromisoformat(row["date"].strip()),
                        "ndvi": float(row["ndvi"]),
                        "validpixelratio": float(row["validpixelratio"]),
                        "qualitystatus": row["qualitystatus"].strip().lower(),
                    }
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Ligne CSV invalide {line_number} : {exc}") from exc

    return sorted(observations, key=lambda item: item["date"])


def is_usable(observation):
    return (
        observation["qualitystatus"] == "usable"
        and observation["validpixelratio"] >= MIN_VALID_PIXELS_RATIO
    )


def classify_change(delta_ndvi):
    if abs(delta_ndvi) < STABLE_DELTA_NDVI:
        return "stable"
    if delta_ndvi >= IMPORTANT_DELTA_NDVI:
        return "hausse_importante"
    if delta_ndvi >= STABLE_DELTA_NDVI:
        return "hausse_moderee"
    if delta_ndvi <= -IMPORTANT_DELTA_NDVI:
        return "baisse_importante_a_examiner"
    return "baisse_moderee_a_examiner"


def confidence_from_quality(previous, current):
    min_ratio = min(previous["validpixelratio"], current["validpixelratio"])
    if min_ratio >= HIGH_CONFIDENCE_PIXELS_RATIO:
        return "high"
    if min_ratio >= MIN_VALID_PIXELS_RATIO:
        return "medium"
    return "low"


def score_from_delta(delta_ndvi):
    """Score transparent de 0 a 100 base sur l'amplitude de variation NDVI."""
    return round(min(abs(delta_ndvi) / IMPORTANT_DELTA_NDVI, 1.0) * 100, 1)


def build_report(observations):
    usable = [item for item in observations if is_usable(item)]

    base_report = {
        "analysis_type": "explainable_ndvi_change_v1",
        "model_type": "rule_based_not_trained_ml",
        "input_file": INPUT_CSV.name,
        "thresholds": {
            "minimum_valid_pixels_ratio": MIN_VALID_PIXELS_RATIO,
            "high_confidence_pixels_ratio": HIGH_CONFIDENCE_PIXELS_RATIO,
            "stable_delta_ndvi": STABLE_DELTA_NDVI,
            "important_delta_ndvi": IMPORTANT_DELTA_NDVI,
        },
        "limitations": [
            "Aide a l'interpretation : ce rapport ne constitue pas un diagnostic agronomique.",
            "Le NDVI seul ne permet pas d'identifier la cause d'une hausse ou d'une baisse.",
            "Les seuils V1 sont des seuils de demonstration configurables.",
            "Une serie historique multi-annuelle est necessaire pour une anomalie statistique robuste.",
        ],
    }

    if len(usable) < 2:
        return {
            **base_report,
            "status": "donnees_insuffisantes",
            "confidence": "insufficient",
            "usable_observations_count": len(usable),
            "explanation": [
                "Au moins deux observations exploitables sont necessaires pour calculer un changement.",
            ],
        }

    previous, current = usable[-2], usable[-1]
    days = (current["date"] - previous["date"]).days
    if days <= 0:
        return {
            **base_report,
            "status": "donnees_insuffisantes",
            "confidence": "insufficient",
            "usable_observations_count": len(usable),
            "explanation": [
                "Les deux dernieres observations exploitables ne permettent pas un intervalle temporel positif.",
            ],
        }

    delta_ndvi = current["ndvi"] - previous["ndvi"]
    status = classify_change(delta_ndvi)
    confidence = confidence_from_quality(previous, current)

    direction = "augmente" if delta_ndvi > 0 else "diminue" if delta_ndvi < 0 else "reste identique"
    explanation = [
        "Deux observations successives de qualite suffisante ont ete comparees.",
        f"Le NDVI {direction} de {abs(delta_ndvi):.4f} sur {days} jour(s).",
        f"La variation journaliere est de {delta_ndvi / days:.6f} NDVI/jour.",
        f"Le statut est determine par des seuils explicites ; aucun modele ML entraine n'est utilise.",
        "La cause du changement ne peut pas etre determinee a partir du NDVI seul.",
    ]

    return {
        **base_report,
        "status": status,
        "confidence": confidence,
        "change_score_0_100": score_from_delta(delta_ndvi),
        "usable_observations_count": len(usable),
        "period": {
            "from": previous["date"].isoformat(),
            "to": current["date"].isoformat(),
            "days": days,
        },
        "ndvi": {
            "from": round(previous["ndvi"], 4),
            "to": round(current["ndvi"], 4),
            "delta": round(delta_ndvi, 4),
            "daily_change": round(delta_ndvi / days, 6),
        },
        "data_quality": {
            "from_valid_pixels_ratio": round(previous["validpixelratio"], 4),
            "to_valid_pixels_ratio": round(current["validpixelratio"], 4),
            "from_valid_pixels_pct": round(previous["validpixelratio"] * 100, 2),
            "to_valid_pixels_pct": round(current["validpixelratio"] * 100, 2),
            "from_status": previous["qualitystatus"],
            "to_status": current["qualitystatus"],
        },
        "explanation": explanation,
    }


def print_summary(report):
    print("\nPhytoPulse Change Intelligence - V1")
    print("=" * 52)
    print(f"Statut      : {report['status']}")
    print(f"Confiance   : {report['confidence']}")

    if "period" not in report:
        print("Analyse     : impossible faute de deux observations exploitables.")
        return

    period = report["period"]
    ndvi = report["ndvi"]
    quality = report["data_quality"]
    print(f"Periode     : {period['from']} -> {period['to']} ({period['days']} jours)")
    print(f"NDVI        : {ndvi['from']:.4f} -> {ndvi['to']:.4f}")
    print(f"Variation   : {ndvi['delta']:+.4f} ({ndvi['daily_change']:+.6f} NDVI/jour)")
    print(f"Score       : {report['change_score_0_100']:.1f}/100")
    print(
        "Qualite     : "
        f"{quality['from_valid_pixels_pct']:.2f}% -> {quality['to_valid_pixels_pct']:.2f}% pixels valides"
    )
    print("Limite      : signal de changement, pas diagnostic de cause.")


def main():
    try:
        observations = read_observations(INPUT_CSV)
        report = build_report(observations)
        OUTPUT_JSON_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print_summary(report)
        print(f"\nRapport JSON cree : {OUTPUT_JSON_PATH}")
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()