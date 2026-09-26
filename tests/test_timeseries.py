"""Tests for PhytoPulse synthetic time-series helpers."""

import pandas as pd
import pytest

from src.timeseries import (
    QUALITY_THRESHOLD,
    REQUIRED_COLUMNS,
    build_synthetic_timeseries,
    quality_status_from_ratio,
    validate_timeseries,
)


def test_build_synthetic_timeseries_has_expected_rows() -> None:
    """The synthetic dataset should contain twelve observations."""
    dataframe = build_synthetic_timeseries()

    assert len(dataframe) == 12


def test_build_synthetic_timeseries_has_required_columns() -> None:
    """The synthetic dataset should expose all required columns."""
    dataframe = build_synthetic_timeseries()

    assert tuple(dataframe.columns) == REQUIRED_COLUMNS


def test_build_synthetic_timeseries_dates_are_sorted() -> None:
    """The synthetic dataset should be ordered by date."""
    dataframe = build_synthetic_timeseries()

    assert dataframe["date"].is_monotonic_increasing


def test_quality_status_rejects_low_valid_pixel_ratio() -> None:
    """Ratios below the threshold should be rejected."""
    assert quality_status_from_ratio(0.39) == "not_usable"


def test_quality_status_accepts_threshold_value() -> None:
    """The threshold value itself should be accepted."""
    assert quality_status_from_ratio(QUALITY_THRESHOLD) == "usable"


def test_build_synthetic_timeseries_marks_all_rows_as_synthetic() -> None:
    """Every demo row must be explicitly marked as synthetic."""
    dataframe = build_synthetic_timeseries()

    assert dataframe["is_synthetic"].eq(True).all()


def test_validate_timeseries_accepts_synthetic_dataset() -> None:
    """The generated synthetic dataset should pass validation."""
    validate_timeseries(build_synthetic_timeseries())


def test_validate_timeseries_rejects_out_of_range_ndvi() -> None:
    """NDVI values outside the valid index range should be rejected."""
    dataframe = build_synthetic_timeseries()
    dataframe.loc[0, "ndvi"] = 1.1

    with pytest.raises(ValueError, match="NDVI"):
        validate_timeseries(dataframe)


def test_validate_timeseries_rejects_unsorted_dates() -> None:
    """A time series with unsorted dates should be rejected."""
    dataframe = build_synthetic_timeseries()
    dataframe.loc[0, "date"] = pd.Timestamp("2026-12-31")

    with pytest.raises(ValueError, match="Dates"):
        validate_timeseries(dataframe)