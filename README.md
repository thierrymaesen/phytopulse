---
title: PhytoPulse
emoji: 🌿
colorFrom: green
colorTo: yellow
sdk: static
pinned: false
license: mit
---

<div align="center">

  <a href="#french">🇫🇷 Version française</a> | <a href="#english">🇬🇧 English version</a>

</div>

---

<a name="french"></a>

# 🌿 PhytoPulse — Détection explicable du stress de végétation

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![NDVI](https://img.shields.io/badge/NDVI-remote%20sensing-2e7d32.svg)](https://earthobservatory.nasa.gov/features/MeasuringVegetation)
[![Weather](https://img.shields.io/badge/weather-Meteostat-4c8bf5.svg)](https://meteostat.net/)
[![Dashboard](https://img.shields.io/badge/dashboard-HTML%2FJavaScript-orange.svg)](dashboard/vegetation_change_dashboard.html)
[![Explainable AI](https://img.shields.io/badge/AI-explainable-7b1fa2.svg)](#-explicabilit%C3%A9-et-limites)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 📖 Présentation

PhytoPulse est un démonstrateur de télédétection appliquée à l'agriculture. Le projet combine l'évolution du NDVI, un contexte météorologique régional et des règles explicables afin de produire un signal de changement de végétation compréhensible et exploitable pour une première vérification terrain.

L'objectif n'est pas de remplacer une expertise agronomique. PhytoPulse transforme plutôt des indicateurs techniques en une synthèse lisible : évolution du NDVI, niveau de confiance, score de changement, contexte chaud ou sec, anomalie historique et consigne de vérification sur la parcelle.

La démonstration utilise une parcelle de référence située à Vielsalm, en Belgique, avec les coordonnées configurées dans `field_config.json`. Le dashboard permet d'ouvrir le centre de la zone dans OpenStreetMap et rappelle explicitement les limites de l'analyse.

## 🎯 Objectifs du projet

- Détecter une variation récente du NDVI à partir d'observations temporelles.
- Comparer le NDVI actuel avec une normale historique multi-annuelle.
- Ajouter un contexte météo régional à l'interprétation.
- Distinguer un signal de changement d'un diagnostic de cause.
- Produire des rapports JSON reproductibles et lisibles.
- Orienter une vérification terrain sans prétendre localiser une sous-zone précise.

## 🚀 Fonctionnalités principales

- **Analyse du changement NDVI** — Compare les observations NDVI utilisables, calcule la variation absolue et journalière, puis attribue un statut explicite comme « baisse modérée à examiner ».
- **Détection d'anomalies** — Compare la période récente à une normale historique synthétique et combine l'écart NDVI avec un indicateur de déficit hydrique climatique.
- **Contexte météo** — Récupère des données météorologiques via Meteostat, les agrège au jour et estime l'ET0 avec Hargreaves-Samani.
- **Explication automatique** — Génère `explain_report.json` à partir des rapports NDVI, météo et anomalie. Les statuts techniques sont convertis en formulations compréhensibles.
- **Orientation terrain** — Affiche le nom de la parcelle, la latitude, la longitude et un lien OpenStreetMap vers le centre de la zone à vérifier.
- **Dashboard sans build** — Interface HTML, CSS et JavaScript vanilla, directement servie par un serveur HTTP local.

## 📸 Dashboard

Le dashboard présente successivement :

- la zone à vérifier sur le terrain ;
- le changement NDVI et son intervalle d'analyse ;
- le contexte météo ;
- l'anomalie détectée ;
- l'explication en langage naturel ;
- les limites et précautions d'interprétation.

Pour lancer le dashboard localement :

```powershell
py -m http.server 8000
```

Puis ouvrir :

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## 🧩 Pipeline de données

Le pipeline principal est orchestré par `run_phytopulse.py` :

```text
1. vegetation_change_engine.py
2. weather_fetcher.py
3. weather_context_engine.py
4. anomaly_engine.py
5. explain_report.py
```

Les fichiers de sortie sont générés dans `data/` :

```text
data/
├── vegetation_change_report.json
├── weather_timeseries.csv
├── weather_context_report.json
├── anomaly_report.json
└── explain_report.json
```

Les rapports générés automatiquement sont ignorés par Git. Les jeux de données de démonstration reproductibles restent versionnés.

## 🗺️ Architecture du projet

```text
phytopulse/
├── dashboard/
│   └── vegetation_change_dashboard.html
├── data/
│   ├── ndvi_timeseries.csv
│   ├── ndvi_history_3ans.csv
│   └── weather_history_3ans.csv
├── src/
│   ├── anomaly_engine.py
│   ├── explain_report.py
│   ├── vegetation_change_engine.py
│   ├── weather_context_engine.py
│   └── weather_fetcher.py
├── build_ndvi_history.py
├── build_weather_history.py
├── field_config.json
├── run_phytopulse.py
├── requirements.txt
├── PROJECT_RULES.md
└── README.md
```

Les anciennes versions de travail sont conservées localement dans `work/archives/` et ne font pas partie du dépôt Git principal.

## ⚙️ Installation

### Environnement Python local

```powershell
git clone [https://github.com/thierrymaesen/phytopulse.git](https://github.com/thierrymaesen/phytopulse.git)
cd phytopulse

py -m venv .venv
.venv\Scripts\Activate.ps1

py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### Générer les historiques de démonstration

```powershell
py .\build_ndvi_history.py
py .\build_weather_history.py
```

`build_weather_history.py` utilise les coordonnées de `field_config.json` et récupère un historique météorologique régional via Meteostat.

### Exécuter le pipeline

```powershell
py .\run_phytopulse.py
```

### Consulter le dashboard

Dans une autre fenêtre PowerShell, depuis la racine du projet :

```powershell
py -m http.server 8000
```

Ouvrir ensuite :

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## 🧪 Tests

Les tests historiques du projet sont conservés dans `tests/`. Pour les exécuter :

```powershell
py -m pytest tests -v
```

Le pipeline de démonstration peut également être vérifié manuellement avec :

```powershell
py .\run_phytopulse.py
```

## 🧠 Explicabilité et limites

PhytoPulse utilise des règles explicites et des statistiques descriptives ; il ne s'agit pas d'un modèle ML entraîné pour produire un diagnostic agronomique.

- Le NDVI seul ne permet pas d'identifier la cause d'une hausse ou d'une baisse.
- Les données météo sont régionales et ne correspondent pas nécessairement à une mesure sur la parcelle.
- Une cooccurrence entre baisse du NDVI et période sèche ne prouve pas une causalité.
- Les coordonnées indiquent le centre approximatif de la zone ; la version actuelle ne localise pas une sous-zone précise.
- Les résultats doivent être confirmés par une observation terrain et, si nécessaire, par une expertise agronomique.

> **PhytoPulse détecte et explique un signal ; il ne remplace pas un diagnostic agronomique.**

## 📊 Données de démonstration

Les données de démonstration sont clairement séparées des données opérationnelles :

- `ndvi_timeseries.csv` contient la série récente utilisée pour le changement.
- `ndvi_history_3ans.csv` contient un historique NDVI synthétique reproductible.
- `weather_history_3ans.csv` contient l'historique météo utilisé pour la démonstration.
- `field_config.json` contient le label et les coordonnées de la parcelle de démonstration.

Les données synthétiques et les seuils V1 servent à illustrer le fonctionnement du pipeline ; ils ne représentent pas une décision agronomique réelle.

## 🔮 Évolutions possibles

- Ajouter le contour réel de la parcelle en GeoJSON ou KML.
- Calculer une heatmap NDVI intra-parcellaire.
- Identifier les sous-zones prioritaires à inspecter.
- Ajouter une interface de sélection de parcelle.
- Remplacer les données synthétiques par des séries Sentinel-2 validées.
- Ajouter des tests dédiés aux rapports NDVI, météo et anomalie.
- Publier une démonstration web hébergée.

## 👨‍💻 Auteur et crédits

**Thierry Maesen**

- GitHub : [@thierrymaesen](https://github.com/thierrymaesen)
- Localisation : Belgique
- Données météo : [Meteostat](https://meteostat.net/)
- Observation de la Terre : concepts NDVI et télédétection
- Cartographie : [OpenStreetMap](https://www.openstreetmap.org/)

Projet réalisé à des fins éducatives et de démonstration de portfolio.

## 📜 Licence

Ce projet est distribué sous licence MIT. Voir le fichier `LICENSE` si celui-ci est présent dans le dépôt.

---

<a name="english"></a>

# 🇬🇧 PhytoPulse — Explainable vegetation change detection

PhytoPulse is a demonstrator for **remote sensing applied to agriculture**. It combines NDVI evolution, regional weather context and explicit rule-based analysis to produce an understandable vegetation-change signal and support an initial field inspection.

The project is not intended to replace agronomic expertise. It translates technical indicators into an interpretable summary: NDVI evolution, confidence level, change score, warm or dry weather context, historical anomaly and field-check guidance.

The demonstration uses a reference field near Vielsalm, Belgium, with coordinates stored in `field_config.json`. The dashboard displays the field location, links to OpenStreetMap and clearly states the limits of the analysis.

## 🎯 Project goals

- Detect recent NDVI variation from usable time-series observations.
- Compare current NDVI with a multi-year historical baseline.
- Add regional weather context to the interpretation.
- Separate a vegetation-change signal from a causal diagnosis.
- Generate reproducible and readable JSON reports.
- Support field inspection without claiming precise within-field localization.

## 🚀 Main features

- **NDVI change analysis** with explicit thresholds and data-quality checks.
- **Anomaly detection** combining historical NDVI deviation and a climate water-deficit proxy.
- **Weather context** retrieved from Meteostat and aggregated daily.
- **Automatic explanation report** generated from the pipeline outputs.
- **Field-location guidance** with latitude, longitude and an OpenStreetMap link.
- **Zero-build dashboard** using HTML, CSS and vanilla JavaScript.

## 📸 Dashboard

The dashboard sequentially presents:

- the field area to inspect;
- the NDVI change and its analysis window;
- the weather context;
- the detected anomaly;
- the natural-language explanation;
- the limits and interpretation caveats.

To run the dashboard locally:

```powershell
py -m http.server 8000
```

Then open:

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## 🧩 Data pipeline

The main pipeline is orchestrated by `run_phytopulse.py`:

```text
1. vegetation_change_engine.py
2. weather_fetcher.py
3. weather_context_engine.py
4. anomaly_engine.py
5. explain_report.py
```

Output files are generated in `data/`:

```text
data/
├── vegetation_change_report.json
├── weather_timeseries.csv
├── weather_context_report.json
├── anomaly_report.json
└── explain_report.json
```

Automatically generated reports are ignored by Git. Reproducible demonstration datasets remain versioned.

## 🗺️ Project architecture

```text
phytopulse/
├── dashboard/
│   └── vegetation_change_dashboard.html
├── data/
│   ├── ndvi_timeseries.csv
│   ├── ndvi_history_3ans.csv
│   └── weather_history_3ans.csv
├── src/
│   ├── anomaly_engine.py
│   ├── explain_report.py
│   ├── vegetation_change_engine.py
│   ├── weather_context_engine.py
│   └── weather_fetcher.py
├── build_ndvi_history.py
├── build_weather_history.py
├── field_config.json
├── run_phytopulse.py
├── requirements.txt
├── PROJECT_RULES.md
└── README.md
```

Old working versions are kept locally in `work/archives/` and are not part of the main Git repository.

## ⚙️ Installation

### Local Python environment

```powershell
git clone [https://github.com/thierrymaesen/phytopulse.git](https://github.com/thierrymaesen/phytopulse.git)
cd phytopulse

py -m venv .venv
.venv\Scripts\Activate.ps1

py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### Generate demonstration histories

```powershell
py .\build_ndvi_history.py
py .\build_weather_history.py
```

`build_weather_history.py` uses the coordinates from `field_config.json` and fetches regional weather history via Meteostat.

### Run the pipeline

```powershell
py .\run_phytopulse.py
```

### View the dashboard

In another PowerShell window, from the project root:

```powershell
py -m http.server 8000
```

Then open:

```text
http://localhost:8000/dashboard/vegetation_change_dashboard.html
```

## 🧪 Tests

Historical project tests are kept in `tests/`. To run them:

```powershell
py -m pytest tests -v
```

The demonstration pipeline can also be checked manually with:

```powershell
py .\run_phytopulse.py
```

## 🧠 Explainability and limitations

PhytoPulse relies on explicit rules and descriptive statistics. It is not a trained ML model providing an agronomic diagnosis.

- NDVI alone cannot identify the cause of a vegetation increase or decrease.
- Weather data is regional and may not represent measurements at field level.
- Co-occurrence between a lower NDVI and dry weather does not prove causality.
- The current coordinates identify the approximate field centre, not a precise sub-zone.
- Results must be confirmed through field observation and, when needed, agronomic expertise.

> **PhytoPulse detects and explains a signal; it does not replace an agronomic diagnosis.**

## 📊 Demonstration data

Demonstration data are clearly separated from operational data:

- `ndvi_timeseries.csv` contains the recent series used for change detection.
- `ndvi_history_3ans.csv` contains a synthetic, reproducible NDVI history.
- `weather_history_3ans.csv` contains the weather history used for the demo.
- `field_config.json` contains the label and coordinates of the demo field.

Synthetic data and V1 thresholds illustrate how the pipeline works; they do not represent a real agronomic decision.

## 🔮 Possible evolutions

- Add the real field boundary as GeoJSON or KML.
- Compute an intra-field NDVI heatmap.
- Identify priority sub-zones to inspect.
- Add a parcel selection interface.
- Replace synthetic data with validated Sentinel-2 series.
- Add dedicated tests for NDVI, weather and anomaly reports.
- Publish a hosted web demo.

## 👨‍💻 Author and credits

**Thierry Maesen**

- GitHub: [@thierrymaesen](https://github.com/thierrymaesen)
- Location: Belgium
- Weather data: [Meteostat](https://meteostat.net/)
- Earth observation: NDVI and remote sensing concepts
- Mapping: [OpenStreetMap](https://www.openstreetmap.org/)

Educational and portfolio demonstration project.

## 📜 License

This project is distributed under the MIT License. See the `LICENSE` file if present in the repository.
