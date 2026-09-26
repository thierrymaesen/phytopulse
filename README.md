# Fix encoding test\n\n---
title: Phytopulse
emoji: ðŸŒ¿
colorFrom: green
colorTo: yellow
sdk: static
pinned: false
license: mit
---

<div align="center">

  <a href="#french">ðŸ‡«ðŸ‡· Version franÃ§aise</a> | <a href="#english">ðŸ‡¬ðŸ‡§ English version</a>

</div>

---

<a name="french"></a>

# ðŸŒ¿ PhytoPulse â€” DÃ©tection explicable du stress de vÃ©gÃ©tation

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![NDVI](https://img.shields.io/badge/NDVI-remote%20sensing-2e7d32.svg)](https://earthobservatory.nasa.gov/features/MeasuringVegetation)
[![Weather](https://img.shields.io/badge/weather-Meteostat-4c8bf5.svg)](https://meteostat.net/)
[![Dashboard](https://img.shields.io/badge/dashboard-HTML%2FJavaScript-orange.svg)](dashboard/vegetation_change_dashboard.html)
[![Explainable AI](https://img.shields.io/badge/AI-explainable-7b1fa2.svg)](#-explicabilitÃ©-et-limites)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## ðŸ“– PrÃ©sentation

PhytoPulse est un dÃ©monstrateur de **tÃ©lÃ©dÃ©tection appliquÃ©e Ã  l'agriculture**. Le projet combine l'Ã©volution du NDVI, un contexte mÃ©tÃ©orologique rÃ©gional et des rÃ¨gles explicables afin de produire un signal de changement de vÃ©gÃ©tation comprÃ©hensible et exploitable pour une premiÃ¨re vÃ©rification terrain.

L'objectif n'est pas de remplacer une expertise agronomique. PhytoPulse transforme plutÃ´t des indicateurs techniques en une synthÃ¨se lisible : Ã©volution du NDVI, niveau de confiance, score de changement, contexte chaud ou sec, anomalie historique et consigne de vÃ©rification sur la parcelle.

La dÃ©monstration utilise une parcelle de rÃ©fÃ©rence situÃ©e Ã  Vielsalm, en Belgique, avec les coordonnÃ©es configurÃ©es dans `field_config.json`. Le dashboard permet d'ouvrir le centre de la zone dans OpenStreetMap et rappelle explicitement les limites de l'analyse.

## ðŸŽ¯ Objectifs du projet

- DÃ©tecter une variation rÃ©cente du NDVI Ã  partir d'observations temporelles.
- Comparer le NDVI actuel avec une normale historique multi-annuelle.
- Ajouter un contexte mÃ©tÃ©o rÃ©gional Ã  l'interprÃ©tation.
- Distinguer un signal de changement d'un diagnostic de cause.
- Produire des rapports JSON reproductibles et lisibles.
- Orienter une vÃ©rification terrain sans prÃ©tendre localiser une sous-zone prÃ©cise.

## ðŸš€ FonctionnalitÃ©s principales

ðŸŒ± **Analyse du changement NDVI** â€” Compare les observations NDVI utilisables, calcule la variation absolue et journaliÃ¨re, puis attribue un statut explicite comme Â« baisse modÃ©rÃ©e Ã  examiner Â».

ðŸ§  **DÃ©tection d'anomalies** â€” Compare la pÃ©riode rÃ©cente Ã  une normale historique synthÃ©tique et combine l'Ã©cart NDVI avec un indicateur de dÃ©ficit hydrique climatique.

ðŸŒ¦ï¸ **Contexte mÃ©tÃ©o** â€” RÃ©cupÃ¨re des donnÃ©es mÃ©tÃ©orologiques via Meteostat, les agrÃ¨ge au jour et estime l'ET0 avec Hargreaves-Samani.

ðŸ“ **Explication automatique** â€” GÃ©nÃ¨re `explain_report.json` Ã  partir des rapports NDVI, mÃ©tÃ©o et anomalie. Les statuts techniques sont convertis en formulations comprÃ©hensibles.

ðŸ“ **Orientation terrain** â€” Affiche le nom de la parcelle, la latitude, la longitude et un lien OpenStreetMap vers le centre de la zone Ã  vÃ©rifier.

ðŸ“Š **Dashboard sans build** â€” Interface HTML, CSS et JavaScript vanilla, directement servie par un serveur HTTP local.

## ðŸ“¸ Dashboard

Le dashboard prÃ©sente successivement :

- la zone Ã  vÃ©rifier sur le terrain ;
- le changement NDVI et son intervalle d'analyse ;
- le contexte mÃ©tÃ©o ;
- l'anomalie dÃ©tectÃ©e ;
- l'explication en langage naturel ;
- les limites et prÃ©cautions d'interprÃ©tation.

Pour lancer le dashboard localement :

```powershell
py -m http.server 8000
```

Puis ouvrir :

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## ðŸ§© Pipeline de donnÃ©es

Le pipeline principal est orchestrÃ© par `run_phytopulse.py` :

```text
1. vegetation_change_engine.py
2. weather_fetcher.py
3. weather_context_engine.py
4. anomaly_engine.py
5. explain_report.py
```

Les fichiers de sortie sont gÃ©nÃ©rÃ©s dans `data/` :

```text
data/
â”œâ”€â”€ vegetation_change_report.json
â”œâ”€â”€ weather_timeseries.csv
â”œâ”€â”€ weather_context_report.json
â”œâ”€â”€ anomaly_report.json
â””â”€â”€ explain_report.json
```

Les rapports gÃ©nÃ©rÃ©s automatiquement sont ignorÃ©s par Git. Les jeux de donnÃ©es de dÃ©monstration reproductibles restent versionnÃ©s.

## ðŸ—ï¸ Architecture du projet

```text
phytopulse/
â”œâ”€â”€ dashboard/
â”‚   â””â”€â”€ vegetation_change_dashboard.html
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ ndvi_timeseries.csv
â”‚   â”œâ”€â”€ ndvi_history_3ans.csv
â”‚   â””â”€â”€ weather_history_3ans.csv
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ anomaly_engine.py
â”‚   â”œâ”€â”€ explain_report.py
â”‚   â”œâ”€â”€ vegetation_change_engine.py
â”‚   â”œâ”€â”€ weather_context_engine.py
â”‚   â””â”€â”€ weather_fetcher.py
â”œâ”€â”€ build_ndvi_history.py
â”œâ”€â”€ build_weather_history.py
â”œâ”€â”€ field_config.json
â”œâ”€â”€ run_phytopulse.py
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ PROJECT_RULES.md
â””â”€â”€ README.md
```

Les anciennes versions de travail sont conservÃ©es localement dans `work/archives/` et ne font pas partie du dÃ©pÃ´t Git principal.

## âš™ï¸ Installation

### Environnement Python local

```powershell
git clone https://github.com/thierrymaesen/phytopulse.git
cd phytopulse

py -m venv .venv
.venv\Scripts\Activate.ps1

py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### GÃ©nÃ©rer les historiques de dÃ©monstration

```powershell
py .\build_ndvi_history.py
py .\build_weather_history.py
```

`build_weather_history.py` utilise les coordonnÃ©es de `field_config.json` et rÃ©cupÃ¨re un historique mÃ©tÃ©orologique rÃ©gional via Meteostat.

### ExÃ©cuter le pipeline

```powershell
py .\run_phytopulse.py
```

### Consulter le dashboard

Dans une autre fenÃªtre PowerShell, depuis la racine du projet :

```powershell
py -m http.server 8000
```

Ouvrir ensuite :

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## ðŸ§ª Tests

Les tests historiques du projet sont conservÃ©s dans `tests/`. Pour les exÃ©cuter :

```powershell
py -m pytest tests -v
```

Le pipeline de dÃ©monstration peut Ã©galement Ãªtre vÃ©rifiÃ© manuellement avec :

```powershell
py .\run_phytopulse.py
```

## ðŸ§  ExplicabilitÃ© et limites

PhytoPulse utilise des rÃ¨gles explicites et des statistiques descriptives ; il ne s'agit pas d'un modÃ¨le ML entraÃ®nÃ© pour produire un diagnostic agronomique.

- Le NDVI seul ne permet pas d'identifier la cause d'une hausse ou d'une baisse.
- Les donnÃ©es mÃ©tÃ©o sont rÃ©gionales et ne correspondent pas nÃ©cessairement Ã  une mesure sur la parcelle.
- Une cooccurrence entre baisse du NDVI et pÃ©riode sÃ¨che ne prouve pas une causalitÃ©.
- Les coordonnÃ©es indiquent le centre approximatif de la zone ; la version actuelle ne localise pas une sous-zone prÃ©cise.
- Les rÃ©sultats doivent Ãªtre confirmÃ©s par une observation terrain et, si nÃ©cessaire, par une expertise agronomique.

> **PhytoPulse dÃ©tecte et explique un signal ; il ne remplace pas un diagnostic agronomique.**

## ðŸ“ DonnÃ©es de dÃ©monstration

Les donnÃ©es de dÃ©monstration sont clairement sÃ©parÃ©es des donnÃ©es opÃ©rationnelles :

- `ndvi_timeseries.csv` contient la sÃ©rie rÃ©cente utilisÃ©e pour le changement.
- `ndvi_history_3ans.csv` contient un historique NDVI synthÃ©tique reproductible.
- `weather_history_3ans.csv` contient l'historique mÃ©tÃ©o utilisÃ© pour la dÃ©monstration.
- `field_config.json` contient le label et les coordonnÃ©es de la parcelle de dÃ©monstration.

Les donnÃ©es synthÃ©tiques et les seuils V1 servent Ã  illustrer le fonctionnement du pipeline ; ils ne reprÃ©sentent pas une dÃ©cision agronomique rÃ©elle.

## ðŸ”® Ã‰volutions possibles

- Ajouter le contour rÃ©el de la parcelle en GeoJSON ou KML.
- Calculer une heatmap NDVI intra-parcellaire.
- Identifier les sous-zones prioritaires Ã  inspecter.
- Ajouter une interface de sÃ©lection de parcelle.
- Remplacer les donnÃ©es synthÃ©tiques par des sÃ©ries Sentinel-2 validÃ©es.
- Ajouter des tests dÃ©diÃ©s aux rapports NDVI, mÃ©tÃ©o et anomalie.
- Publier une dÃ©monstration web hÃ©bergÃ©e.

## ðŸ‘¨â€ðŸ’» Auteur et crÃ©dits

**Thierry Maesen**

- GitHub : [@thierrymaesen](https://github.com/thierrymaesen)
- Localisation : Belgique
- DonnÃ©es mÃ©tÃ©o : [Meteostat](https://meteostat.net/)
- Observation de la Terre : concepts NDVI et tÃ©lÃ©dÃ©tection
- Cartographie : [OpenStreetMap](https://www.openstreetmap.org/)

Projet rÃ©alisÃ© Ã  des fins Ã©ducatives et de dÃ©monstration de portfolio.

## ðŸ“œ Licence

Ce projet est distribuÃ© sous licence MIT. Voir le fichier `LICENSE` si celui-ci est prÃ©sent dans le dÃ©pÃ´t.

---

<a name="english"></a>

# ðŸ‡¬ðŸ‡§ PhytoPulse â€” Explainable vegetation change detection

PhytoPulse is a demonstrator for **remote sensing applied to agriculture**. It combines NDVI evolution, regional weather context and explicit rule-based analysis to produce an understandable vegetation-change signal and support an initial field inspection.

The project is not intended to replace agronomic expertise. It translates technical indicators into an interpretable summary: NDVI evolution, confidence level, change score, warm or dry weather context, historical anomaly and field-check guidance.

The demonstration uses a reference field near Vielsalm, Belgium, with coordinates stored in `field_config.json`. The dashboard displays the field location, links to OpenStreetMap and clearly states the limits of the analysis.

## ðŸŽ¯ Project goals

- Detect recent NDVI variation from usable time-series observations.
- Compare current NDVI with a multi-year historical baseline.
- Add regional weather context to the interpretation.
- Separate a vegetation-change signal from a causal diagnosis.
- Generate reproducible and readable JSON reports.
- Support field inspection without claiming precise within-field localization.

## ðŸš€ Main features

- **NDVI change analysis** with explicit thresholds and data-quality checks.
- **Anomaly detection** combining historical NDVI deviation and a climate water-deficit proxy.
- **Weather context** retrieved from Meteostat and aggregated daily.
- **Automatic explanation report** generated from the pipeline outputs.
- **Field-location guidance** with latitude, longitude and an OpenStreetMap link.
- **Zero-build dashboard** using HTML, CSS and vanilla JavaScript.

## ðŸ—ï¸ Pipeline

The main pipeline is orchestrated by `run_phytopulse.py`:

```text
vegetation_change_engine.py
weather_fetcher.py
weather_context_engine.py
anomaly_engine.py
explain_report.py
```

Run it with:

```powershell
py .\run_phytopulse.py
```

Start the dashboard with:

```powershell
py -m http.server 8000
```

Then open:

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## ðŸ§  Explainability and limitations

PhytoPulse relies on explicit rules and descriptive statistics. It is not a trained ML model providing an agronomic diagnosis.

- NDVI alone cannot identify the cause of a vegetation increase or decrease.
- Weather data is regional and may not represent measurements at field level.
- Co-occurrence between a lower NDVI and dry weather does not prove causality.
- The current coordinates identify the approximate field centre, not a precise sub-zone.
- Results must be confirmed through field observation and, when needed, agronomic expertise.

> **PhytoPulse detects and explains a signal; it does not replace an agronomic diagnosis.**

## ðŸ‘¨â€ðŸ’» Author and credits

**Thierry Maesen**

- GitHub: [@thierrymaesen](https://github.com/thierrymaesen)
- Weather data: [Meteostat](https://meteostat.net/)
- Mapping: [OpenStreetMap](https://www.openstreetmap.org/)

Educational and portfolio demonstration project.

## ðŸ“œ License

This project is distributed under the MIT License. See `LICENSE` if present.


