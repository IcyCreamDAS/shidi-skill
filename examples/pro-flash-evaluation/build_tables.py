#!/usr/bin/env python3
"""Build four tables per case from direct ChatGPT and original Kimi ratings."""
import argparse
from copy import deepcopy
import csv
import hashlib
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
    """Apply the original evidence/autonomy aggregation rule to weighted points."""
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


def current_scores(case):
    original = read_json(BASE / case / "evaluation.json")
    review = read_json(BASE / "independent-review/scores.json")
    weights = review["weights"]
    ratings = {r["condition"]: r for r in review["rows"] if r["case"] == case}
    assert set(ratings) == set(ARMS) and set(weights) == set(REVIEW_LABELS) and sum(weights.values()) == 100
    assert review["evaluator"].startswith("ChatGPT")
    for row in ratings.values():
        assert set(row["grades"]) == set(weights)
        assert all(type(v) is int and 0 <= v <= 4 for v in row["grades"].values())
        assert row["weighted_scores"] == {k: weights[k] * row["grades"][k] / 4 for k in weights}
        assert sum(row["weighted_scores"].values()) == row["total"]
        report = BASE / "independent-review" / row["source_report"]
        assert hashlib.sha256(report.read_bytes()).hexdigest() == row["source_sha256"]
    inputs = deepcopy(original)
    keys = dict(zip(DEPTH_LABELS, REVIEW_LABELS))
    inputs["depth"] = {"weights": {k: weights[v] for k, v in keys.items()},
                       "arms": {a: {k: ratings[a]["weighted_scores"][v] for k, v in keys.items()} for a in ARMS}}
    computed = compute(inputs)
    computed.update(evaluator={"depth": review["evaluator"], "workflow": original["provenance"]["evaluator"],
                               "aggregate": "calculated; not an independent reviewer"},
                    status="direct_chatgpt_original_kimi_and_derived_aggregate",
                    current_chatgpt_source="../independent-review/scores.json",
                    current_chatgpt_totals={a: ratings[a]["total"] for a in ARMS},
                    aggregate_rule={"unchanged": ["Q", "M", "F", "S"],
                                    "E": "(ChatGPT_E + Kimi_evidence_points * 20 / 25) / 2",
                                    "A": "(ChatGPT_A + Kimi_autonomy_points) / 2",
                                    "total": "sum of six weighted points; not the mean of reviewer totals"})
    for arm in ARMS:
        for system in ("depth", "aggregate"):
            computed["axes"][arm][system] = dict(zip(REVIEW_LABELS.values(), computed["axes"][arm][system].values()))
    return original, ratings, computed


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
    content, ratings, computed = current_scores(case)
    review = read_json(BASE / "independent-review/scores.json")
    weights = review["weights"]
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
    rubric_table(target / "kimi-rubric.md", "Kimi 评分细则：九项工作流", workflow_rows, WORKFLOW_LABELS,
                 "沿用原始Kimi独立工作流评分，分值未重打；原分项见evaluation.json。九项在雷达图中按既有分组归为六轴：探索；证据可靠性+分层；PDF；两项主题判据；综合+失效边界；自主。各轴按组内权重归一到0–100。")
    totals = [{"arm": a, "chatgpt_content_review": ratings[a]["total"],
               "kimi_workflow": computed["totals"][a]["workflow"],
               "aggregate_derived": computed["totals"][a]["aggregate"]} for a in ARMS]
    write_csv(target / "final-scores.csv", ["arm", "chatgpt_content_review", "kimi_workflow", "aggregate_derived"], totals)
    text = ["# 最终评分：两位评分者与派生汇总", "", "| 条件 | ChatGPT 直接复评 /100 | Kimi 工作流 /100 | 汇总（公式计算）/100 |", "|---|---:|---:|---:|"]
    text += [f"| {r['arm']} | {r['chatgpt_content_review']:.2f} | {r['kimi_workflow']:.2f} | {r['aggregate_derived']:.2f} |" for r in totals]
    text += ["", "ChatGPT分数来自[真实复评](../independent-review/scores.json)，Kimi工作流分来自evaluation.json。均为既有输出的事后评价，每条件一次运行；不是平台成绩。",
             "汇总沿用原公式，以真实ChatGPT分项替换早期Kimi科研深度分：Q/M/F/S保持ChatGPT加权分；E=(ChatGPT证据分+Kimi证据两项合计×20/25)÷2；A=(ChatGPT透明分+Kimi自主分)÷2；最后六项相加。汇总不是第三位评分者，也不是两个总分的平均值。旧数值另存historical-computed-scores.json。", ""]
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
    (target / "historical-computed-scores.json").write_text(json.dumps(compute(content), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return computed


def build_readme(output_root):
    text = ["# Pro / Flash / without：每轮四张表、三张图", "",
            "本页完整展示两轮真实运行：第一题顺序逻辑、第四题损伤记忆。每轮依次为ChatGPT评分细则、Kimi评分细则、最终评分、用量四张表，以及ChatGPT、Kimi、汇总三张六维图。表格均有MD/CSV，图均有PNG/SVG。", "",
            "**ChatGPT分项由ChatGPT于2026-10-27直接复评既有输出**，源数据与报告哈希见[独立复评数据](independent-review/scores.json)，0–4档判据见[RUBRIC.md](independent-review/RUBRIC.md)。Kimi表沿用原工作流评分。汇总按原公式计算并换入真实ChatGPT分项，不能称为ChatGPT直接评分或第三位独立评阅。", "",
            "执行模型统一为K2.8 Preview + max；Pro固定`b28eb4e`，Flash固定`6e03d72`，without不加载Skill。各组独立会话，每条件一次；评分为事后、非盲内容评价，不是平台成绩，不作稳定增益或统计显著性结论。", ""]
    cases = (("sequential-logic", "第一题：顺序化学逻辑", "材料能不能只在‘先光照、后遇湿’时才打开？"),
             ("damage-memory", "第四题：涂层损伤记忆", "涂层能不能像打过疫苗一样，第一次划伤后，第二次修复得更快？"))
    tables = (("chatgpt-rubric", "1. ChatGPT评分细则表"), ("kimi-rubric", "2. Kimi评分细则表"),
              ("final-scores", "3. 最终评分表"), ("usage", "4. 实际用量表"))
    charts = (("chatgpt", "ChatGPT六维内容复评"), ("kimi", "Kimi六维工作流评分"),
              ("aggregate", "汇总六维图（公式计算）"))
    for case, title, question in cases:
        text += ["## " + title, "", "> " + question, "", f"原始任务、报告与轨迹：[Pro]({case}/pro/) · [Flash]({case}/flash/) · [without]({case}/without/)。", ""]
        for name, heading in tables:
            body = (output_root / case / f"{name}.md").read_text(encoding="utf-8").split("\n", 1)[1].strip()
            body = body.replace("](../independent-review/", "](independent-review/")
            text += ["### " + heading, "", body, "", f"下载：[MD]({case}/{name}.md) · [CSV]({case}/{name}.csv)", ""]
        for name, heading in charts:
            path = f"{case}/{name}-six-dimensions"
            text += ["### " + heading, "", f"![{title}：{heading}]({path}.png)", "", f"下载：[PNG]({path}.png) · [SVG]({path}.svg)", ""]
    text += ["## 计算、来源与复现", "",
             "ChatGPT六项权重依次为15/25/20/20/10/10，分项=权重×0–4档÷4；其图展示原始0–4档。Kimi表保留九项原分，图按表下注明的分组压为六轴；汇总图也为六轴，二者均归一到各轴满分100。图的轴和标度不同，不能用多边形面积比较评分体系。", "",
             "每轮computed-scores.json保存当前三套总分和图轴，historical-computed-scores.json保留早期Kimi科研深度分及其旧汇总；evaluation.json与RESULTS.md作为原始Kimi评阅记录保留。原始科研输出、运行前协议与执行用量不因事后复评重写。费用无逐次扣费字段时保留null。", "",
             "在仓库根目录运行：", "", "```bash", "python examples/pro-flash-evaluation/build_tables.py",
             "python -m pip install matplotlib numpy", "python examples/pro-flash-evaluation/make_figures.py", "```", "",
             "build_tables.py使用标准库，核对ChatGPT档位、分数和源报告哈希，并同时生成四表与本README；make_figures.py复制真实ChatGPT原图，按相同数据重绘Kimi及汇总图。可用--out指定导出目录、--font指定中文字体。", "",
             "[独立复评量表及重绘方法](independent-review/README.md) · [顺序逻辑原始Kimi评阅](sequential-logic/RESULTS.md) · [损伤记忆原始Kimi评阅](damage-memory/RESULTS.md)", ""]
    (output_root / "README.md").write_text("\n".join(text), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=BASE, help="output root; original data are read from this checkout")
    args = parser.parse_args()
    for case in CASES:
        result = build_case(case, args.out)
        print(case, json.dumps(result["totals"], ensure_ascii=False))
    build_readme(args.out)


if __name__ == "__main__":
    main()
