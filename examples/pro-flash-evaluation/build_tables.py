#!/usr/bin/env python3
"""Publish direct ChatGPT review tables; retain explicitly historical Kimi data."""
import argparse
import csv
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
CASES = ("sequential-logic", "damage-memory")
ARMS = ("pro", "flash", "without")
REVIEW_LABELS = dict(Q="问题保真", M="机制与因果", E="原始证据", F="证伪与对照", S="路线与下一步", A="透明与可审计")
DEPTH_LABELS = {
    "question": "问题保真", "mechanism": "机制与因果", "evidence": "原始证据",
    "falsification": "证伪与对照", "synthesis": "综合路线", "autonomy": "透明与自主",
}
WORKFLOW_LABELS = {
    "exploration": "探索覆盖", "evidence_reliability": "证据可靠性",
    "evidence_separation": "证据分层", "pdf_delivery": "PDF 交付",
    "synthesis": "综合交付", "autonomy": "交互与自主",
    "topic_1": "顺序逻辑", "topic_2": "状态保持",
    "damage_memory": "损伤记忆", "second_acceleration": "第二次修复加速",
    "distinction_failure": "概念区分与失效边界",
}
WORKFLOW_AXES = ("探索覆盖", "证据可靠与分层", "PDF 交付", "主题判据", "综合与失效边界", "交互与自主")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def compute(content):
    """Keep historical ratings; derive totals and explicitly labelled axes."""
    weights = content["depth"]["weights"]
    if set(weights) != set(DEPTH_LABELS) or sum(weights.values()) != 100:
        raise ValueError("invalid depth weights")
    rows = content["workflow"]["nine_dimensions"]
    if len({r["id"] for r in rows}) != len(rows) or sum(r["weight"] for r in rows) != 100:
        raise ValueError("invalid workflow dimensions")
    workflow = {r["id"]: r for r in rows}
    topic_ids = ("topic_1", "topic_2") if "topic_1" in workflow else ("damage_memory", "second_acceleration")
    groups = (("exploration",), ("evidence_reliability", "evidence_separation"),
              ("pdf_delivery",), topic_ids, ("synthesis", "distinction_failure"), ("autonomy",))
    result = {"evaluator": content["provenance"]["evaluator"],
              "status": "historical_kimi_ratings_not_current_chatgpt_review", "totals": {}, "axes": {}}
    for arm in ARMS:
        depth = content["depth"]["arms"][arm]
        if set(depth) != set(weights):
            raise ValueError("missing depth scores")
        if any(not 0 <= depth[k] <= weights[k] for k in weights):
            raise ValueError("depth score outside its weight")
        if any(not 0 <= r[arm] <= r["weight"] for r in rows):
            raise ValueError("workflow score outside its weight")
        aggregate = dict(depth)
        evidence_weight = sum(workflow[k]["weight"] for k in ("evidence_reliability", "evidence_separation"))
        evidence = sum(workflow[k][arm] for k in ("evidence_reliability", "evidence_separation"))
        aggregate["evidence"] = (depth["evidence"] + evidence * weights["evidence"] / evidence_weight) / 2
        autonomy = workflow["autonomy"]
        aggregate["autonomy"] = (depth["autonomy"] + autonomy[arm] * weights["autonomy"] / autonomy["weight"]) / 2
        result["totals"][arm] = {"depth": round(sum(depth.values()), 2),
                                 "workflow": round(sum(r[arm] for r in rows), 2),
                                 "aggregate": round(sum(aggregate.values()), 2)}
        result["axes"][arm] = {
            "depth": {DEPTH_LABELS[k]: depth[k] * 100 / weights[k] for k in weights},
            "workflow": {label: sum(workflow[k][arm] for k in group) * 100 / sum(workflow[k]["weight"] for k in group)
                         for label, group in zip(WORKFLOW_AXES, groups)},
            "aggregate": {DEPTH_LABELS[k]: aggregate[k] * 100 / weights[k] for k in weights},
        }
    return result


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rubric_table(path, title, rows, labels, note):
    text = ["# " + title, "", "| 维度 | 权重 | Pro | Flash | without |", "|---|---:|---:|---:|---:|"]
    text += [f"| {labels[r['dimension']]} | {r['weight']} | {r['pro']} | {r['flash']} | {r['without']} |" for r in rows]
    text += ["", note, ""]
    path.write_text("\n".join(text), encoding="utf-8")


def build_case(case, output_root):
    source = BASE / case
    target = output_root / case
    target.mkdir(parents=True, exist_ok=True)
    content = read_json(source / "evaluation.json")
    computed = compute(content)
    review = read_json(BASE / "independent-review/scores.json")
    weights = review["weights"]
    ratings = {r["condition"]: r for r in review["rows"] if r["case"] == case}
    assert set(ratings) == set(ARMS) and sum(weights.values()) == 100
    assert review["evaluator"].startswith("ChatGPT")
    for row in ratings.values():
        assert all(type(v) is int and 0 <= v <= 4 for v in row["grades"].values())
        assert row["weighted_scores"] == {k: weights[k] * row["grades"][k] / 4 for k in weights}
        assert sum(row["weighted_scores"].values()) == row["total"]
    computed["current_chatgpt_totals"] = {a: ratings[a]["total"] for a in ARMS}
    computed["current_chatgpt_source"] = "../independent-review/scores.json"
    depth_rows = [{"dimension": k, "weight": weight,
                   **{a: ratings[a]["weighted_scores"][k] for a in ARMS}} for k, weight in weights.items()]
    workflow_rows = [{"dimension": r["id"], "weight": r["weight"], **{a: r[a] for a in ARMS}}
                     for r in content["workflow"]["nine_dimensions"]]
    fields = ["dimension", "weight", *ARMS]
    # Keep existing ChatGPT URLs, now backed by the direct review instead of Kimi ratings.
    write_csv(target / "chatgpt-rubric.csv", fields, depth_rows)
    write_csv(target / "kimi-rubric.csv", fields, workflow_rows)
    rubric_table(target / "chatgpt-rubric.md", "ChatGPT 直接复评：六维加权分项", depth_rows, REVIEW_LABELS,
                 "ChatGPT于2026-10-27直接复评既有输出；事后、非盲、单人内容评价。表中为权重×0–4档÷4后的分项得分。原档位、总分与报告哈希见[独立复评数据](../independent-review/scores.json)。")
    rubric_table(target / "kimi-rubric.md", "历史工作流评分细则（Kimi）", workflow_rows, WORKFLOW_LABELS,
                 "本表是Kimi历史评分，不是当前ChatGPT直接复评。原分值见evaluation.json；当前主评分见final-scores.md。")
    totals = [{"arm": a, "chatgpt_content_review": ratings[a]["total"]} for a in ARMS]
    write_csv(target / "final-scores.csv", ["arm", "chatgpt_content_review"], totals)
    text = ["# ChatGPT 直接复评：当前主评分", "", "| 条件 | ChatGPT 六维内容复评 |", "|---|---:|"]
    text += [f"| {r['arm']} | {r['chatgpt_content_review']:.2f} |" for r in totals]
    text += ["", "来源：[真实分项、评分者与报告哈希](../independent-review/scores.json)。各维0–4档，权重15/25/20/20/10/10；2026-10-27事后非盲复评，每条件一次运行。不是官方成绩。",
             "历史Kimi评分及派生综合分保留在evaluation.json、computed-scores.json与RESULTS.md中，不能标为ChatGPT直接评分，也不与本表混合。", ""]
    (target / "final-scores.md").write_text("\n".join(text), encoding="utf-8")
    usages = []
    for arm in ARMS:
        state = read_json(source / arm / "run.json")
        verify = read_json(source / arm / "output/pdf-verification.json")
        tokens = state["tokens"]
        usages.append({"arm": arm, "inputOther": tokens["inputOther"], "output": tokens["output"],
                       "cacheRead": tokens["inputCacheRead"], "cacheCreation": tokens["inputCacheCreation"],
                       "wall_seconds": state["wall_time_seconds_total"], "questions": state["coordinator_question_rounds"],
                       "pdf": verify["pdf_count"], "cost": state["cost"]})
    fields = ["arm", "inputOther", "output", "cacheRead", "cacheCreation", "wall_seconds", "questions", "pdf", "cost"]
    write_csv(target / "usage.csv", fields, usages)
    text = ["# 实际用量与交付", "", "| 组别 | inputOther | output | 缓存读取 | 缓存创建 | Agent 总墙钟(s) | 问答 | 核验 PDF | 人民币 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    text += [f"| {r['arm']} | {r['inputOther']} | {r['output']} | {r['cacheRead']} | {r['cacheCreation']} | {r['wall_seconds']} | {r['questions']} | {r['pdf']} | 无逐次扣费字段 |" for r in usages]
    text += ["", "来源为各组 run.json 与 pdf-verification.json。token/cache 为日志累计值；墙钟取 Agent 工具回执，包含续跑。金额保留 null。", ""]
    (target / "usage.md").write_text("\n".join(text), encoding="utf-8")
    (target / "computed-scores.json").write_text(json.dumps(computed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return computed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE, help="output root; original data are read from this checkout")
    args = parser.parse_args()
    for case in CASES:
        result = build_case(case, args.out)
        print(case, json.dumps({"ChatGPT_direct_review": result["current_chatgpt_totals"],
                                "historical_Kimi": result["totals"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
