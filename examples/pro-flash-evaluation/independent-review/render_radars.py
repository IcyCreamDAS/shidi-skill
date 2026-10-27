#!/usr/bin/env python3
"""Render independent six-dimensional ratings, tables and a two-case overview."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np

BASE = Path(__file__).resolve().parent
CASES = {"sequential-logic": "顺序化学逻辑", "damage-memory": "涂层损伤记忆"}
DIMENSIONS = {"Q": "问题保真", "M": "机制与因果", "E": "原始证据", "F": "证伪与对照", "S": "路线与下一步", "A": "透明与可审计"}
ENGLISH = dict(Q="Question", M="Mechanism", E="Evidence", F="Falsification", S="Next steps", A="Auditability")
ARMS = ("pro", "flash", "without")
NAMES = dict(pro="Pro", flash="Flash", without="without Skill")
COLORS = dict(pro="#0072B2", flash="#009E73", without="#D98200")
MARKERS = dict(pro="o", flash="^", without="s")
STYLES = dict(pro="-", flash="--", without=":")


def load_scores(check_sources=True):
    data = json.loads((BASE / "scores.json").read_text(encoding="utf-8"))
    assert sum(data["weights"].values()) == 100
    assert set(data["weights"]) == set(DIMENSIONS)
    assert hashlib.sha256((BASE / "RUBRIC.md").read_bytes()).hexdigest() == data["rubric_sha256"]
    assert len(data["rows"]) == 6
    assert {(r["case"], r["condition"]) for r in data["rows"]} == {(c, a) for c in CASES for a in ARMS}
    for row in data["rows"]:
        assert set(row["grades"]) == set(DIMENSIONS)
        assert all(type(v) is int and 0 <= v <= 4 for v in row["grades"].values())
        expected = {d: row["grades"][d] * data["weights"][d] / 4 for d in DIMENSIONS}
        assert expected == row["weighted_scores"]
        assert sum(expected.values()) == row["total"]
        if check_sources:
            source = BASE / row["source_report"]
            assert hashlib.sha256(source.read_bytes()).hexdigest() == row["source_sha256"]
    return data


def setup_font(font):
    if font:
        font_manager.fontManager.addfont(str(font))
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font)).get_name()
        return True
    available = {f.name for f in font_manager.fontManager.ttflist}
    for candidate in ("Noto Sans CJK SC", "Microsoft YaHei", "SimHei"):
        if candidate in available:
            plt.rcParams["font.family"] = candidate
            return True
    plt.rcParams["font.family"] = "DejaVu Sans"
    return False


def draw(ax, case, data, chinese):
    theta = np.linspace(0, 2 * np.pi, len(DIMENSIONS), endpoint=False).tolist()
    closed = theta + theta[:1]
    for arm in ARMS:
        row = next(r for r in data["rows"] if r["case"] == case and r["condition"] == arm)
        values = [row["grades"][d] for d in DIMENSIONS]
        ax.plot(closed, values + values[:1], color=COLORS[arm], linestyle=STYLES[arm],
                linewidth=2.1, marker=MARKERS[arm], markersize=5.5,
                label=f"{NAMES[arm]}  {row['total']:.2f}")
        ax.fill(closed, values + values[:1], color=COLORS[arm], alpha=.035)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    labels = [f"{DIMENSIONS[d] if chinese else ENGLISH[d]}\n({data['weights'][d]}%)" for d in DIMENSIONS]
    ax.set_xticks(theta, labels)
    ax.tick_params(axis="x", pad=13, labelsize=10)
    ax.set_ylim(0, 4.10)
    ax.set_yticks([1, 2, 3, 4], ["1", "2", "3", "4"])
    ax.tick_params(axis="y", labelsize=8, colors="#777777")
    ax.set_rlabel_position(15)
    ax.grid(color="#9ca3af", alpha=.35, linewidth=.6)
    ax.spines["polar"].set_color("#b5bdc7")


def save(fig, path):
    for suffix in ("png", "svg"):
        target = path.with_suffix("." + suffix)
        fig.savefig(target, dpi=220, facecolor="white", metadata={"Date": None} if suffix == "svg" else None)
        if suffix == "svg":
            target.write_text("\n".join(line.rstrip() for line in target.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path)
    parser.add_argument("--out", type=Path, default=BASE)
    parser.add_argument("--scores-only", action="store_true", help="replot a standalone scoring export; original source hashes remain recorded but are not verified")
    args = parser.parse_args()
    data = load_scores(check_sources=not args.scores_only)
    chinese = setup_font(args.font)
    plt.rcParams.update({"axes.unicode_minus": False, "legend.frameon": False, "font.size": 11,
                         "svg.hashsalt": "shidi-independent-six-dimensions"})
    args.out.mkdir(parents=True, exist_ok=True)
    foot = "ChatGPT 内容复评 · 各轴 0–4 档 · 总分按标注权重计算" if chinese else "ChatGPT content review; axes 0-4; totals use the stated weights"
    for case, title in CASES.items():
        fig = plt.figure(figsize=(8.5, 8.7))
        ax = fig.add_axes([.21, .25, .58, .57], projection="polar")
        draw(ax, case, data, chinese)
        fig.suptitle((title if chinese else case) + "\n" + ("六维科研深度" if chinese else "Six-dimensional research depth"), y=.96, fontsize=16, linespacing=1.5)
        fig.legend(*ax.get_legend_handles_labels(), loc="lower center", bbox_to_anchor=(.5, .105), ncol=3, fontsize=10)
        fig.text(.5, .04, foot, ha="center", fontsize=9, color="#555555")
        save(fig, args.out / (case + "-radar"))
        rows = [r for r in data["rows"] if r["case"] == case]
        with (args.out / (case + "-scores.csv")).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["condition", *DIMENSIONS, "total"], lineterminator="\n")
            writer.writeheader()
            for row in rows: writer.writerow({"condition": row["condition"], **row["grades"], "total": row["total"]})
        text = ["# " + title + "：ChatGPT 六维内容复评", "", "| 条件 | Q | M | E | F | S | A | 总分 |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
        text += ["| " + r["condition"] + " | " + " | ".join(str(r["grades"][d]) for d in DIMENSIONS) + f" | {r['total']:.2f} |" for r in rows]
        text += ["", "各维0–4档；权重依次15/25/20/20/10/10。评分为2026-10-27的事后、非盲内容复评。执行模型统一K2.8 Preview + max，每条件一次运行。"]
        (args.out / (case + "-scores.md")).write_text("\n".join(text) + "\n", encoding="utf-8")
    fig = plt.figure(figsize=(14.5, 8.0))
    for i, (case, title) in enumerate(CASES.items()):
        ax = fig.add_axes([.10 + .49 * i, .27, .31, .55], projection="polar")
        draw(ax, case, data, chinese)
        ax.set_title(title if chinese else case, pad=45, fontsize=15)
        ax.legend(loc="lower center", bbox_to_anchor=(.5, -.33), ncol=1, fontsize=10, labelspacing=.35)
    fig.suptitle("从灵感到研究问题：两组六维内容复评" if chinese else "From an idea to a research question", y=.98, fontsize=18)
    fig.text(.5, .035, foot, ha="center", fontsize=10, color="#555555")
    save(fig, args.out / "two-case-radars")
    print("Validated six scores; rendered two individual radar charts and the two-case overview (PNG + SVG).")


if __name__ == "__main__":
    main()
