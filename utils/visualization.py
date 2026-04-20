"""
utils/visualization.py

Helpers for generating change-detection visualizations.

Dependencies:
    pip install matplotlib numpy pillow
"""

from __future__ import annotations
from typing import Optional, List, Tuple
import io
import base64


def delta_colormap(
    delta: "np.ndarray",
    vmin: float = -0.5,
    vmax: float = 0.5,
    cmap: str = "RdYlGn",
    title: str = "Index Delta",
    figsize: Tuple[int, int] = (8, 6),
) -> bytes:
    """
    Render a delta raster as a coloured PNG.
    Returns raw PNG bytes (write to file or send as HTTP response).

    Requires: pip install matplotlib numpy
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        import numpy as np
    except ImportError:
        raise ImportError("Install matplotlib: pip install matplotlib")

    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    im = ax.imshow(delta, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="nearest")
    plt.colorbar(im, ax=ax, label="Δ value", fraction=0.046, pad=0.04)
    ax.set_title(title, fontsize=12, pad=10)
    ax.axis("off")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def change_overlay(
    rgb_before: "np.ndarray",
    change_mask: "np.ndarray",
    color: Tuple[int, int, int] = (255, 60, 60),
    alpha: float = 0.5,
) -> bytes:
    """
    Overlay a binary change mask onto an RGB image.
    Returns PNG bytes.

    Args:
        rgb_before : H×W×3 uint8 array
        change_mask: H×W bool array (True = changed pixel)
        color      : RGB colour for changed pixels
        alpha      : blend weight for the overlay

    Requires: pip install pillow numpy
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        raise ImportError("Install pillow and numpy: pip install pillow numpy")

    out = rgb_before.copy().astype(float)
    for i, c in enumerate(color):
        out[:, :, i] = np.where(change_mask, out[:, :, i] * (1 - alpha) + c * alpha, out[:, :, i])

    img = Image.fromarray(np.clip(out, 0, 255).astype("uint8"))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def index_timeseries_chart(
    dates: List[str],
    ndvi_values: List[float],
    ndwi_values: List[float],
    title: str = "Spectral Index Time-Series",
) -> bytes:
    """
    Line chart of NDVI / NDWI over time.
    Returns PNG bytes.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from datetime import datetime
    except ImportError:
        raise ImportError("Install matplotlib: pip install matplotlib")

    parsed = [datetime.fromisoformat(d) for d in dates]

    fig, ax = plt.subplots(figsize=(10, 4), dpi=100)
    ax.plot(parsed, ndvi_values, color="#1D9E75", linewidth=2, marker="o", markersize=4, label="NDVI")
    ax.plot(parsed, ndwi_values, color="#378ADD", linewidth=2, marker="s", markersize=4, label="NDWI")
    ax.axhline(0, color="#888", linewidth=0.5, linestyle="--")
    ax.set_xlabel("Date")
    ax.set_ylabel("Index value")
    ax.set_title(title)
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def png_to_base64(png_bytes: bytes) -> str:
    """Encode PNG bytes to a data-URI for embedding in HTML / JSON."""
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode()
