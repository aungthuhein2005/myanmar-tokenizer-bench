"""The headline chart: Burmese tokens as a multiple of English, per tokenizer.

Rendered twice (light and dark) so the README can swap them with <picture>.
Single series -> one hue, no legend; the title names it. Values sit at the bar tips.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402

THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  grid="#e1e0d9", base="#c3c2b7", bar="#2a78d6"),
    "dark": dict(surface="#1a1a19", ink="#ffffff", ink2="#c3c2b7", muted="#898781",
                 grid="#2c2c2a", base="#383835", bar="#3987e5"),
}
FONT = ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"]


def _bar(ax, y: float, width: float, height: float, radius: float, color: str) -> None:
    """Horizontal bar: square at the baseline, rounded at the data end."""
    x0, x1, y0, y1 = 0.0, width, y - height / 2, y + height / 2
    r = min(radius, width / 2)
    verts = [(x0, y0), (x1 - r, y0), (x1, y0), (x1, y0 + height * 0.18),
             (x1, y1 - height * 0.18), (x1, y1), (x1 - r, y1), (x0, y1), (x0, y0)]
    codes = [MplPath.MOVETO, MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3,
             MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3, MplPath.LINETO, MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=color, edgecolor="none", zorder=3))


def bar_chart(items: list[tuple[str, float]], out: Path, theme: str, *, title: str, subtitle: str,
              fmt: str, reference: tuple[float, str] | None) -> Path:
    """items: (label, value). Sorted worst (largest) first, top to bottom.
    Labels may have a second line ("name\\n= other models with the same tokenizer")."""
    t = THEMES[theme]
    items = sorted(items, key=lambda kv: kv[1])  # barh draws bottom-up, so worst ends on top
    n = len(items)
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = FONT
    slot = 0.52 if any("\n" in label for label, _ in items) else 0.42

    fig, ax = plt.subplots(figsize=(8.6, 1.25 + slot * n), dpi=200)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])

    xmax = max(v for _, v in items) * 1.14
    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, n - 0.4)
    span = ax.get_xlim()[1]
    for i, (_, value) in enumerate(items):
        _bar(ax, i, value, 0.5, span * 0.008, t["bar"])
        ax.text(value + span * 0.012, i, fmt.format(value), va="center", ha="left",
                fontsize=9.5, color=t["ink"], fontweight="semibold", zorder=4)

    ax.set_yticks(range(n), [label for label, _ in items], fontsize=9.5, color=t["ink2"], linespacing=1.25)
    for tick in ax.get_yticklabels():  # second line = models sharing the tokenizer, smaller
        if "\n" in tick.get_text():
            tick.set_fontsize(8.5)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", colors=t["muted"], labelsize=8.5, length=0)
    tick_fmt = fmt.replace(":.1f", ":g").replace(":.0f", ":g")
    ax.xaxis.set_major_formatter(lambda x, _: tick_fmt.format(x))
    ax.grid(axis="x", color=t["grid"], linewidth=0.8, zorder=0)
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(t["base"])

    if reference:
        x, label = reference
        ax.axvline(x, color=t["muted"], linewidth=1, zorder=2)
        ax.text(x, n - 0.45, f" {label}", color=t["muted"], fontsize=8, va="bottom", ha="left")

    fig.text(0.02, 0.97, title, fontsize=13, fontweight="bold", color=t["ink"], va="top")
    fig.text(0.02, 0.97 - 0.3 / fig.get_figheight(), subtitle, fontsize=9, color=t["ink2"], va="top")
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.62 / fig.get_figheight()))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor=t["surface"])
    plt.close(fig)
    return out
