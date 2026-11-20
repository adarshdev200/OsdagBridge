# =============================================================================
# OsdagBridge Report — charts
#
# Matplotlib charts generated while the report is being built:
#   * utilization ratio (UR = demand / capacity) bar charts for girders, deck
#     slab, cross bracing and end diaphragms  → Section 5.5
#   * material quantity charts (steel tonnage, concrete vs. reinforcement)
#                                            → Chapter 7
# The PNGs are written into the report's temporary build folder and embedded
# with a PyLaTeX Figure. Colours / sizes come from styles.THEME.
# =============================================================================

import logging
import os
import re
import textwrap
from typing import List, Optional, Sequence, Tuple

from pylatex import Figure, NoEscape

from osdagbridge.core.reports.styles import THEME

logger = logging.getLogger(__name__)

URItem = Tuple[str, Optional[float]]   # (check label, UR or None when not available)


def _new_figure(**kw):
    # Plain Figure + Agg canvas instead of pyplot: the report runs in a worker
    # thread next to the Qt GUI, and pyplot's global state is not thread-safe.
    from matplotlib.figure import Figure as MplFigure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig = MplFigure(**kw)
    FigureCanvasAgg(fig)
    return fig


def _safe_name(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _bar_color(ur: float) -> str:
    c, ch = THEME.colors, THEME.chart
    if ur > ch.ur_limit:
        return c.hex("chart_fail")
    if ur >= ch.ur_warn:
        return c.hex("chart_warn")
    return c.hex("chart_pass")


def _draw_ur_axis(ax, title: str, items: Sequence[URItem]):
    ch, c = THEME.chart, THEME.colors
    labels = [lbl for lbl, _ in items]
    values = [(v if v is not None else 0.0) for _, v in items]
    xs = range(len(items))

    bars = ax.bar(xs, values, width=ch.bar_width,
                  color=[_bar_color(v) for v in values], edgecolor="#333333", linewidth=0.4, zorder=3)
    for b, (_, v) in zip(bars, items):
        txt = "n/a" if v is None else f"{v:.2f}"
        # white box so the UR = 1.0 line never runs through a value
        ax.annotate(txt, (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=ch.font_size - 1, zorder=5,
                    color="#777777" if v is None else "black",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="white", edgecolor="none"))

    ax.axhline(ch.ur_limit, color=c.hex("chart_limit"), linestyle="--", linewidth=1.3,
               zorder=4, label=f"UR = {ch.ur_limit:.1f} (limit)")
    top = max([ch.ur_limit] + values) * 1.18
    ax.set_ylim(0, top)
    ax.set_xticks(list(xs))
    rotate = len(labels) > 4
    if not rotate:
        # few bars: wrap long names onto two lines instead of rotating them
        labels = [textwrap.fill(lbl, 14) for lbl in labels]
    ax.set_xticklabels(labels, rotation=30 if rotate else 0, ha="right" if rotate else "center")
    ax.set_ylabel("Utilization Ratio (D/C)")
    ax.set_title(title)
    ax.legend(loc="upper right")


def ur_chart(out_dir: str, title: str, items: Sequence[URItem], keep_missing: bool = False) -> Optional[str]:
    """One bar chart; returns the PNG path (None if there is nothing to plot).
    Checks without a result are dropped, or shown as "n/a" with keep_missing."""
    if not any(v is not None for _, v in items):
        return None
    if not keep_missing:
        items = [it for it in items if it[1] is not None]
    import matplotlib
    ch = THEME.chart
    with matplotlib.rc_context(ch.rc_params()):
        width = max(ch.width_in * 0.6, min(ch.width_in, 1.0 + 0.75 * len(items)))
        fig = _new_figure(figsize=(width, ch.height_in))
        ax = fig.add_subplot(111)
        _draw_ur_axis(ax, title, items)
        fig.tight_layout()
        path = os.path.join(out_dir, "ur_" + _safe_name(title) + ".png")
        fig.savefig(path)
    return path


def ur_overview_chart(out_dir: str, groups: Sequence[Tuple[str, Sequence[URItem]]]) -> Optional[str]:
    """Governing (max) UR of each element group in a single chart."""
    items: List[URItem] = []
    for name, group in groups:
        vals = [v for _, v in group if v is not None]
        items.append((name, max(vals) if vals else None))
    # all primary elements stay on this chart; one without results reads "n/a"
    return ur_chart(out_dir, "Governing Utilization Ratio by Element", items, keep_missing=True)


def quantity_charts(out_dir: str, steel: Sequence[Tuple[str, float]],
                    concrete_m3: Optional[float], rebar_t: Optional[float]) -> Optional[str]:
    """Two panels: structural steel tonnage per element, and concrete volume
    vs. reinforcement weight (twin axes since the units differ)."""
    steel = [(k, v) for k, v in steel if v is not None]
    if not steel and concrete_m3 is None and rebar_t is None:
        return None
    import matplotlib
    ch, c = THEME.chart, THEME.colors
    with matplotlib.rc_context(ch.rc_params()):
        fig = _new_figure(figsize=(ch.width_in, ch.height_in))
        ax1, ax2 = fig.subplots(1, 2, gridspec_kw={"width_ratios": [1.4, 1]})

        # (a) structural steel
        if steel:
            names = [k for k, _ in steel]
            vals = [v for _, v in steel]
            bars = ax1.bar(names, vals, width=ch.bar_width, color=c.hex("chart_steel"), zorder=3)
            for b, v in zip(bars, vals):
                ax1.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v), xytext=(0, 2),
                             textcoords="offset points", ha="center", va="bottom",
                             fontsize=ch.font_size - 1)
            total = sum(vals)
            ax1.set_ylim(0, max(vals) * 1.2 if max(vals) > 0 else 1)
            ax1.set_title(f"Structural Steel (total {total:.2f} MT)")
        else:
            ax1.text(0.5, 0.5, "No steel quantities", ha="center", va="center", transform=ax1.transAxes)
            ax1.set_title("Structural Steel")
        ax1.set_ylabel("Weight (MT)")

        # (b) concrete vs reinforcement
        ax2.set_title("Deck Slab Materials")
        ax2b = ax2.twinx()
        ax2b.grid(False)
        ax2b.spines["right"].set_visible(True)
        xs = [0, 1]
        cv = concrete_m3 or 0.0
        rv = rebar_t or 0.0
        ax2.bar([xs[0]], [cv], width=ch.bar_width, color=c.hex("chart_concrete"), zorder=3)
        ax2b.bar([xs[1]], [rv], width=ch.bar_width, color=c.hex("chart_rebar"), zorder=3)
        ax2.set_xticks(xs)
        ax2.set_xticklabels(["Concrete", "Reinforcement"])
        ax2.set_ylabel(r"Concrete volume (m$^3$)")
        ax2b.set_ylabel("Reinforcement weight (MT)")
        ax2.set_ylim(0, cv * 1.25 if cv > 0 else 1)
        ax2b.set_ylim(0, rv * 1.25 if rv > 0 else 1)
        if concrete_m3 is not None:
            ax2.annotate(f"{cv:.2f} m³", (xs[0], cv), xytext=(0, 2), textcoords="offset points",
                         ha="center", va="bottom", fontsize=ch.font_size - 1)
        if rebar_t is not None:
            ax2b.annotate(f"{rv:.2f} MT", (xs[1], rv), xytext=(0, 2), textcoords="offset points",
                          ha="center", va="bottom", fontsize=ch.font_size - 1)

        fig.tight_layout()
        path = os.path.join(out_dir, "material_quantities.png")
        fig.savefig(path)
    return path


def figure_tex(path: Optional[str], caption: str, label: Optional[str] = None,
               width: Optional[str] = None) -> str:
    """Embed a generated PNG with a PyLaTeX Figure (empty string if no image)."""
    if not path:
        return ""
    fig = Figure(position="H")
    fig.add_image(path.replace("\\", "/"), width=NoEscape(width or THEME.chart.latex_width))
    fig.add_caption(NoEscape(caption))
    if label:
        fig.append(NoEscape(r"\label{" + label + "}"))
    return "\n" + fig.dumps() + "\n"
