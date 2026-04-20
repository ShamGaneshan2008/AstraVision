"""
utils/image_processing.py

Raster processing helpers for when you connect real imagery.

Dependencies (install when ready):
    pip install rasterio numpy scipy

All functions are pure — they take numpy arrays and return numpy arrays.
This makes them easily testable and composable.
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Spectral indices
# ─────────────────────────────────────────────────────────────────────────────

def compute_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Normalized Difference Vegetation Index."""
    denom = nir.astype(float) + red.astype(float)
    return np.where(denom != 0, (nir - red) / denom, 0.0)


def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Water Index (Gao 1996)."""
    denom = green.astype(float) + nir.astype(float)
    return np.where(denom != 0, (green - nir) / denom, 0.0)


def compute_nbr(nir: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """Normalized Burn Ratio — useful for wildfire / burn scar detection."""
    denom = nir.astype(float) + swir2.astype(float)
    return np.where(denom != 0, (nir - swir2) / denom, 0.0)


def compute_ndbi(swir1: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Normalized Difference Built-up Index — urban expansion proxy."""
    denom = swir1.astype(float) + nir.astype(float)
    return np.where(denom != 0, (swir1 - nir) / denom, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# Change detection
# ─────────────────────────────────────────────────────────────────────────────

def change_mask(
    index_before: np.ndarray,
    index_after: np.ndarray,
    threshold: float = 0.1,
) -> np.ndarray:
    """
    Binary change mask: True where abs(delta) > threshold.
    Returns a bool array the same shape as inputs.
    """
    delta = index_after.astype(float) - index_before.astype(float)
    return np.abs(delta) > threshold


def delta_stats(
    index_before: np.ndarray,
    index_after: np.ndarray,
    nodata: float = -9999.0,
) -> dict:
    """
    Compute summary statistics of the delta raster.
    Excludes nodata values before computing.
    """
    delta = index_after.astype(float) - index_before.astype(float)
    valid = delta[delta != nodata]
    if valid.size == 0:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "changed_pct": 0.0}
    return {
        "mean": float(np.mean(valid)),
        "std":  float(np.std(valid)),
        "min":  float(np.min(valid)),
        "max":  float(np.max(valid)),
        "changed_pct": float(np.mean(np.abs(valid) > 0.1) * 100),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pre-processing
# ─────────────────────────────────────────────────────────────────────────────

def normalize_band(band: np.ndarray, vmin: float = 0.0, vmax: float = 10000.0) -> np.ndarray:
    """Scale a raw integer band to [0, 1] reflectance."""
    return np.clip((band.astype(float) - vmin) / (vmax - vmin), 0.0, 1.0)


def cloud_mask_sentinel2(scl_band: np.ndarray) -> np.ndarray:
    """
    Generate a valid-pixel mask from Sentinel-2 Scene Classification Layer (SCL).
    Valid classes: 4 (vegetation), 5 (bare soil), 6 (water), 7 (unclassified).
    Returns True where pixels are valid (cloud-free).
    """
    valid_classes = {4, 5, 6, 7}
    mask = np.zeros(scl_band.shape, dtype=bool)
    for cls in valid_classes:
        mask |= (scl_band == cls)
    return mask


def coregister_arrays(
    array_ref: np.ndarray,
    array_tgt: np.ndarray,
) -> np.ndarray:
    """
    Naive spatial co-registration by cropping/padding to match shapes.
    In production use rasterio.warp.reproject for proper reprojection.
    """
    h = min(array_ref.shape[0], array_tgt.shape[0])
    w = min(array_ref.shape[1], array_tgt.shape[1])
    return array_tgt[:h, :w]


# ─────────────────────────────────────────────────────────────────────────────
# GeoTIFF I/O (requires rasterio)
# ─────────────────────────────────────────────────────────────────────────────

def read_band(tif_path: str, band_index: int = 1) -> Tuple[np.ndarray, dict]:
    """
    Read a single band from a GeoTIFF.
    Returns (array, profile).

    Requires: pip install rasterio
    """
    try:
        import rasterio  # type: ignore
    except ImportError:
        raise ImportError("Install rasterio: pip install rasterio")
    with rasterio.open(tif_path) as src:
        arr = src.read(band_index).astype(float)
        return arr, src.profile


def write_raster(
    array: np.ndarray,
    out_path: str,
    profile: dict,
) -> None:
    """Write a 2-D numpy array as a single-band GeoTIFF."""
    try:
        import rasterio  # type: ignore
    except ImportError:
        raise ImportError("Install rasterio: pip install rasterio")
    profile.update(count=1, dtype="float32")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(array.astype("float32"), 1)
