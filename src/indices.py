"""Spectral index calculations for PhytoPulse."""

from __future__ import annotations

import numpy as np


def calculate_ndvi(nir: object, red: object) -> float | np.ndarray:
    """Calculate the Normalized Difference Vegetation Index (NDVI).

    NDVI = (NIR - Red) / (NIR + Red)

    A zero denominator is represented by NaN to avoid returning an invalid
    infinite value.
    """
    nir_array = np.asarray(nir, dtype=float)
    red_array = np.asarray(red, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(
            nir_array - red_array,
            nir_array + red_array,
            out=np.full(np.broadcast(nir_array, red_array).shape, np.nan),
            where=(nir_array + red_array) != 0,
        )

    if result.ndim == 0:
        return float(result)

    return result


def calculate_ndmi(nir: object, swir: object) -> float | np.ndarray:
    """Calculate the Normalized Difference Moisture Index (NDMI).

    NDMI = (NIR - SWIR) / (NIR + SWIR)

    A zero denominator is represented by NaN to avoid returning an invalid
    infinite value.
    """
    nir_array = np.asarray(nir, dtype=float)
    swir_array = np.asarray(swir, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        result = np.divide(
            nir_array - swir_array,
            nir_array + swir_array,
            out=np.full(np.broadcast(nir_array, swir_array).shape, np.nan),
            where=(nir_array + swir_array) != 0,
        )

    if result.ndim == 0:
        return float(result)

    return result