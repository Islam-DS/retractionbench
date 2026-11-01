"""Shared visual style for every figure script, following the published figure rules of Nature
(research figure guide), Springer, and Annals of Internal Medicine (Phase 6 figure redesign):

- Arial, 7 pt text and 8 pt bold lowercase panel letters, set at final printed size: figures are
  drawn at the width they print (FULL_WIDTH = the manuscript's 6.5 in text width) and included
  without rescaling, so the point sizes here are the point sizes on the page.
- No titles or explanatory sentences inside a figure; the caption carries them.
- Black text only; color marks identity, never text. No background fills, shadows, or gridlines.
- Okabe-Ito / Wong (2011) colorblind-safe palette. The three hues used together in one plot
  (VERMILLION, BLUE, GREEN) pass the colorblind-separation and contrast checks; ORANGE fails text
  contrast and is only used with a distinct marker shape and a legend.
- Every estimate is shown with its interval; no bars without a measure of variability.

Semantic meaning -> color (same everywhere):
  superseded / retracted evidence  -> VERMILLION
  correction / notice              -> BLUE
  current / replacement evidence   -> GREEN
  everything else                  -> black / gray
Model identity is never color-coded (ADR-169).
"""

import matplotlib.pyplot as plt

INK = "#000000"
GRAY = "#7F7F7F"
LIGHT = "#BFBFBF"

VERMILLION = "#D55E00"
BLUE = "#0072B2"
GREEN = "#009E73"
ORANGE = "#E69F00"

# Names kept so older scripts (the item walkthrough) still import; tints are now near-white,
# so diagram boxes read as outlines rather than colored panels.
RED = VERMILLION
AMBER = ORANGE
EDGE = INK
RED_TINT = AMBER_TINT = BLUE_TINT = GREEN_TINT = GRAY_TINT = "#FFFFFF"
MODEL_NEUTRAL = INK

MM = 1 / 25.4
FULL_WIDTH = 6.5  # inches; the manuscript's text width
FONT_SIZE = 7
PANEL_SIZE = 8
LINE = 0.75


def set_rcparams() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
            "font.size": FONT_SIZE,
            "axes.titlesize": FONT_SIZE,
            "axes.labelsize": FONT_SIZE,
            "xtick.labelsize": FONT_SIZE,
            "ytick.labelsize": FONT_SIZE,
            "legend.fontsize": FONT_SIZE,
            "axes.linewidth": LINE,
            "xtick.major.width": LINE,
            "ytick.major.width": LINE,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "lines.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.grid": False,
            "legend.frameon": False,
            "mathtext.fontset": "custom",
            "mathtext.rm": "Arial",
            "mathtext.it": "Arial:italic",
            "mathtext.bf": "Arial:bold",
            "pdf.fonttype": 42,  # embed TrueType, keep text editable (Nature requirement)
            "ps.fonttype": 42,
            "savefig.dpi": 600,
        }
    )


def panel_label(ax, letter: str, x: float = -0.02, y: float = 1.02) -> None:
    """Bold lowercase panel letter at the top-left corner of an axes (Nature style)."""
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=PANEL_SIZE, fontweight="bold", va="bottom", ha="right")


def save(fig, name: str) -> None:
    fig.savefig(f"{name}.pdf")
    fig.savefig(f"{name}.png", dpi=300)
    plt.close(fig)
    print(f"wrote {name}.pdf")
