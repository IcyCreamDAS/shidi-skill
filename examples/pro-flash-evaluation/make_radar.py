#!/usr/bin/env python3
"""Render paired Pro/Flash/without radar charts from each case's scores-six.csv."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parent
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 200,
    "savefig.dpi": 300, "savefig.bbox": "tight", "legend.frameon": False,
})
CASES = {
    "sequential-logic": "顺序化学逻辑：三组质量—自主性权衡",
}
COLORS = {"pro": "#0072B2", "flash": "#009E73", "without": "#E69F00"}
LABELS = {"pro": "Pro", "flash": "Flash", "without": "without Skill"}
MARKERS = {"pro": "o", "flash": "^", "without": "s"}

for case, title in CASES.items():
    root = BASE / case
    with (root / "scores-six.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    labels = [row["dimension"].replace("（", "\n（") for row in rows]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    closed = angles + angles[:1]
    fig, ax = plt.subplots(figsize=(8.2, 7.2), subplot_kw={"projection": "polar"})
    for arm in ("pro", "flash", "without"):
        values = [float(row[arm]) for row in rows]
        series = values + values[:1]
        ax.plot(closed, series, color=COLORS[arm], linewidth=1.8,
                marker=MARKERS[arm], markersize=4.5, label=LABELS[arm])
        ax.fill(closed, series, color=COLORS[arm], alpha=0.055)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels)
    ax.tick_params(axis="x", pad=17)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100"])
    ax.set_rlabel_position(90)
    ax.grid(color="#888888", alpha=0.24, linewidth=0.6)
    ax.spines["polar"].set_color("#888888")
    ax.spines["polar"].set_linewidth(0.7)
    ax.set_title(title, pad=28)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.24), ncol=3)
    fig.text(0.5, 0.01, "每条件 n=1；同一 K2.8 Preview + max。六维由九项指标合并，时间/token/PDF 另列。",
             ha="center", fontsize=9, color="#555555")
    fig.subplots_adjust(left=0.16, right=0.84, top=0.82, bottom=0.29)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    texts = [(t, t.get_window_extent(renderer)) for t in fig.findobj(matplotlib.text.Text)
             if t.get_text().strip() and t.get_visible()]
    overlaps = [(a.get_text(), b.get_text()) for i, (a, ba) in enumerate(texts)
                for b, bb in texts[i + 1:] if ba.overlaps(bb)]
    if overlaps:
        raise RuntimeError(f"Text overlap in {case}: {overlaps}")
    for text, box in texts:
        frame = fig.bbox
        if box.x0 < frame.x0 or box.y0 < frame.y0 or box.x1 > frame.x1 or box.y1 > frame.y1:
            raise RuntimeError(f"Text outside figure in {case}: {text.get_text()}")
    fig.savefig(root / "six-dimensions.png", facecolor="white")
    fig.savefig(root / "six-dimensions.svg", facecolor="white")
    plt.close(fig)
    print(f"Saved {case}/six-dimensions.png and .svg; no text overlaps")
