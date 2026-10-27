#!/usr/bin/env python3
"""Render six charts from bundled original ratings; no author-machine paths."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from build_tables import BASE, CASES, ARMS, compute, read_json

TITLES = {"sequential-logic": "顺序化学逻辑", "damage-memory": "涂层损伤记忆"}
SYSTEMS = {"depth": ("chatgpt", "科研深度评分 · Kimi 复评"),
           "workflow": ("kimi", "工作流评分 · Kimi"),
           "aggregate": ("aggregate", "综合展示 · 派生值")}
ENGLISH = {"问题保真": "Question fidelity", "机制与因果": "Mechanism",
           "原始证据": "Source evidence", "证伪与对照": "Falsification",
           "综合路线": "Research route", "透明与自主": "Transparency",
           "探索覆盖": "Exploration", "证据可靠与分层": "Evidence",
           "PDF 交付": "PDF delivery", "主题判据": "Topic criteria",
           "综合与失效边界": "Synthesis / limits", "交互与自主": "Autonomy"}
COLORS = {"pro": "#0072B2", "flash": "#009E73", "without": "#E69F00"}
NAMES = {"pro": "Pro", "flash": "Flash", "without": "without Skill"}
MARKERS = {"pro": "o", "flash": "^", "without": "s"}


def render(output_root, font=None):
    if font:
        font_manager.fontManager.addfont(str(font))
        family = font_manager.FontProperties(fname=str(font)).get_name()
        plt.rcParams["font.family"] = family
        chinese = True
    else:
        available = {f.name for f in font_manager.fontManager.ttflist}
        chinese_fonts = [n for n in ("Noto Sans CJK SC", "Microsoft YaHei", "SimHei") if n in available]
        chinese = bool(chinese_fonts)
        plt.rcParams["font.family"] = chinese_fonts[0] if chinese_fonts else "DejaVu Sans"
    plt.rcParams.update({"axes.unicode_minus": False, "font.size": 11,
                         "svg.hashsalt": "shidi-evaluation-v1", "legend.frameon": False})
    for case in CASES:
        content = compute(read_json(BASE / case / "evaluation.json"))
        destination = output_root / case
        destination.mkdir(parents=True, exist_ok=True)
        for system, (filename, title) in SYSTEMS.items():
            labels = list(content["axes"]["pro"][system])
            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
            closed = angles + angles[:1]
            fig = plt.figure(figsize=(8.5, 8.5))
            ax = fig.add_axes([.20, .23, .60, .60], projection="polar")
            for arm in ARMS:
                values = list(content["axes"][arm][system].values())
                series = values + values[:1]
                ax.plot(closed, series, color=COLORS[arm], linewidth=2, marker=MARKERS[arm],
                        markersize=5, label=NAMES[arm])
                ax.fill(closed, series, color=COLORS[arm], alpha=.045)
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            ax.set_xticks(angles, labels if chinese else [ENGLISH[x] for x in labels])
            ax.tick_params(axis="x", pad=16)
            ax.set_ylim(0, 100)
            ax.set_yticks([25, 50, 75, 100])
            ax.set_yticklabels(["25", "50", "75", "100"], fontsize=8, color="#666666")
            ax.set_rlabel_position(15)
            ax.grid(color="#888888", alpha=.25, linewidth=.6)
            ax.spines["polar"].set_color("#aaaaaa")
            heading = TITLES[case] + "\n" + title if chinese else case + "\n" + system + " / Kimi review"
            fig.suptitle(heading, y=.96, fontsize=15, linespacing=1.6)
            fig.legend(*ax.get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(.5, .10), ncol=3)
            note = "同一 K2.8 Preview + max · 每组一次运行 · 两套量表均由 Kimi 评分" if chinese else "Same K2.8 Preview + max; one run per arm; both rubrics scored by Kimi"
            fig.text(.5, .045, note, ha="center", fontsize=9, color="#555555")
            for suffix in ("png", "svg"):
                fig.savefig(destination / f"{filename}-six-dimensions.{suffix}", dpi=220,
                            facecolor="white", metadata={"Date": None} if suffix == "svg" else None)
            plt.close(fig)
            print(f"{case}/{filename}-six-dimensions.png + .svg")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE)
    parser.add_argument("--font", type=Path, help="optional CJK font; otherwise use an installed CJK font or English labels")
    args = parser.parse_args()
    render(args.out, args.font)


if __name__ == "__main__":
    main()
