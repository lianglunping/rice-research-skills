"""Scoped Matplotlib defaults and final-size publication export."""

from math import isfinite
from pathlib import Path

import matplotlib as mpl


AXIS_PT = 0.75
CURVE_PT = 1.0
ERROR_PT = 0.75


def publication_rc(font_family="Arial"):
    """Return settings for use in matplotlib.rc_context during plotting and export."""
    return {
        "font.family": font_family,
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 8,
        "legend.title_fontsize": 8,
        "axes.linewidth": AXIS_PT,
        "xtick.major.width": AXIS_PT,
        "ytick.major.width": AXIS_PT,
        "xtick.minor.width": AXIS_PT,
        "ytick.minor.width": AXIS_PT,
        "lines.linewidth": CURVE_PT,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "pdf.fonttype": 42,
        "pdf.use14corefonts": False,
        "text.usetex": False,
        "savefig.bbox": None,
    }


def save_publication_figure(fig, filename, width_mm, height_mm, dpi=300):
    """Set the figure canvas to its final size and save one PDF or PNG."""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".png"}:
        raise ValueError("filename must end in .pdf or .png")
    for label, value in (("width_mm", width_mm), ("height_mm", height_mm), ("dpi", dpi)):
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{label} must be finite and positive")

    fig.set_size_inches(width_mm / 25.4, height_mm / 25.4, forward=False)
    # Neutralize a caller's automatic tight crop without changing global rc settings.
    with mpl.rc_context({"savefig.bbox": None}):
        fig.savefig(filename, format=suffix[1:], dpi=dpi, transparent=False, facecolor="white")
