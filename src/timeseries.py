"""Synthetic time-series helpers for PhytoPulse."""

from __future__ import annotations

import pandas as pd

QUALITY_THRESHOLD = 0.70

REQUIRED_COLUMNS = (
    "date",
    "ndvi",
    "ndmi",
    "valid_pixel_ratio",
    "quality_status",
    "is_synthetic",
)


def build_synthetic_timeseries() -> pd.DataFrame:
    """Return a synthetic vegetation time series for local pipeline testing."""
    records = [
        ("2026-04-05", 0.42, 0.18, 0.96),
        ("2026-04-19", 0.48, 0.21, 0.93),
        ("2026-05-03", 0.56, 0.27, 0.91),
        ("2026-05-17", 0.63, 0.31, 0.88),
        ("2026-05-31", 0.69, 0.34, 0.82),
        ("2026-06-14", 0.71, 0.36, 0.76),
        ("2026-06-28", 0.70, 0.33, 0.39),
        ("2026-07-12", 0.67, 0.28, 0.84),
        ("2026-07-26", 0.64, 0.21, 0.86),
        ("2026-08-09", 0.60, 0.15, 0.89),
        ("2026-08-23", 0.58, 0.12, 0.92),
        ("2026-09-06", 0.53, 0.17, 0.90),
    ]

    dataframe = pd.DataFrame(
        records,
        columns=("date", "ndvi", "ndmi", "valid_pixel_ratio"),
    )
    dataframe["date"] = pd.to_datetime(dataframe["date"])
    dataframe["quality_status"] = dataframe["valid_pixel_ratio"].map(
        quality_status_from_ratio
    )
    dataframe["is_synthetic"] = True

    return dataframe


def quality_status_from_ratio(valid_pixel_ratio: float) -> str:
    """Return the quality status for a valid-pixel ratio."""
    if valid_pixel_ratio >= QUALITY_THRESHOLD:
        return "usable"

    return "not_usable"


def validate_timeseries(dataframe: pd.DataFrame) -> None:
    """Validate the minimum structure and value ranges of a time series."""
    missing_columns = set(REQUIRED_COLUMNS) - set(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )

    if not dataframe["date"].is_monotonic_increasing:
        raise ValueError("Dates must be sorted in increasing order.")

    for index_name in ("ndvi", "ndmi"):
        if not dataframe[index_name].between(-1.0, 1.0).all():
            raise ValueError(f"{index_name.upper()} values must be between -1 and 1.")

    if not dataframe["valid_pixel_ratio"].between(0.0, 1.0).all():
        raise ValueError("Valid-pixel ratios must be between 0 and 1.")

    if not dataframe["is_synthetic"].eq(True).all():
        raise ValueError("This demonstration dataset must be marked as synthetic.")