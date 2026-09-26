"""Tests for PhytoPulse spectral index calculations."""

import numpy as np

from src.indices import calculate_ndmi, calculate_ndvi


def test_calculate_ndvi_scalar() -> None:
    """NDVI should be correct for scalar input values."""
    result = calculate_ndvi(nir=0.8, red=0.2)

    assert np.isclose(result, 0.6)


def test_calculate_ndmi_scalar() -> None:
    """NDMI should be correct for scalar input values."""
    result = calculate_ndmi(nir=0.8, swir=0.2)

    assert np.isclose(result, 0.6)


def test_calculate_ndvi_array() -> None:
    """NDVI should support vector inputs."""
    result = calculate_ndvi(nir=[0.8, 0.2], red=[0.2, 0.2])

    np.testing.assert_allclose(result, [0.6, 0.0])


def test_calculate_ndmi_array() -> None:
    """NDMI should support vector inputs."""
    result = calculate_ndmi(nir=[0.8, 0.2], swir=[0.2, 0.2])

    np.testing.assert_allclose(result, [0.6, 0.0])


def test_calculate_ndvi_zero_denominator_returns_nan() -> None:
    """NDVI should return NaN instead of infinity for zero denominator."""
    result = calculate_ndvi(nir=0.0, red=0.0)

    assert np.isnan(result)


def test_calculate_ndmi_zero_denominator_returns_nan() -> None:
    """NDMI should return NaN instead of infinity for zero denominator."""
    result = calculate_ndmi(nir=0.0, swir=0.0)

    assert np.isnan(result)