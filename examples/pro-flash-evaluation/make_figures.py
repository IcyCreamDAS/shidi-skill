#!/usr/bin/env python3
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parent
data = json.loads((BASE.parent / "shidi-evaluation-review-20261027/computed-scores.json").read_text(encoding="utf-8"))
weights = json.loads((BASE.parent / "shidi-evaluation-review-20261027/scores.json").read_text(encoding="utf-8"))["weights"]
keys = list(weights)
labels = ["问题保真", "机制与因果", "原始证据", "证伪与对照", "综合路线", "透明与自主"]
colors = {"pro": "#0072B2", "flash": "#009E73", "without": "#E69F00"}
names = {"pro": "Pro", "flash": "Flash", "without": "without Skill"}
markers = {"pro": "o", "flash": "^", "without": "s"}
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                     "axes.unicode_minus": False, "font.size": 10, "figure.dpi": 180,
                     "savefig.dpi": 260, "savefig.bbox": "tight", "legend.frameon": False})
kimi_axes = {
    "pro": [100, 85, 100, 100, 100, 25],
    "flash": [100, 60, 100, 60, 100, 100],
    "without": [100, 35, 100, 45, 87.5, 100],
}
for system, title in (("chatgpt", "ChatGPT 权重续评：顺序逻辑"),
                      ("kimi", "Kimi 修正评分：顺序逻辑"),
                      ("aggregate", "三大体系汇总：顺序逻辑")):
    fig, ax = plt.subplots(figsize=(8.1, 7.1), subplot_kw={"projection": "polar"})
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    closed = angles + angles[:1]
    for arm in ("pro", "flash", "without"):
        raw = data["systems"][system]["sequential_logic"][arm]
        if system == "chatgpt":
            values = [raw[key] / weights[key] * 100 for key in keys]
        elif system == "aggregate":
            values = [raw[key] / weights[key] * 100 for key in keys]
        else:
            values = kimi_axes[arm]
        series = values + values[:1]
        ax.plot(closed, series, color=colors[arm], linewidth=1.9, marker=markers[arm], markersize=5, label=names[arm])
        ax.fill(closed, series, color=colors[arm], alpha=0.055)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels)
    ax.tick_params(axis="x", pad=18)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0", "25", "50", "75", "100"])
    ax.set_rlabel_position(90)
    ax.grid(color="#888888", alpha=0.24, linewidth=0.6)
    ax.spines["polar"].set_color("#888888")
    ax.spines["polar"].set_linewidth(0.7)
    ax.set_title(title, pad=28)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.20), ncol=3)
    fig.text(0.5, 0.01, "每条件 n=1；同一 K2.8 Preview + max。时间/token/PDF 另列。",
             ha="center", fontsize=9, color="#555555")
    fig.subplots_adjust(left=0.16, right=0.84, top=0.82, bottom=0.24)
    fig.savefig(BASE / "sequential-logic" / f"{system}-six-dimensions.png", facecolor="white")
    fig.savefig(BASE / "sequential-logic" / f"{system}-six-dimensions.svg", facecolor="white")
    plt.close(fig)
    print(f"Saved sequential-logic/{system}-six-dimensions.png and .svg")
