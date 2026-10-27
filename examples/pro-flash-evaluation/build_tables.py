#!/usr/bin/env python3
from pathlib import Path
import csv
import json
import os

BASE = Path(__file__).resolve().parent
EVALUATION_ROOT = Path(os.environ.get("SHIDI_EVALUATION_ROOT", str(Path.home() / "AGENTDATA/kimicode")))
SOURCES = {
    "sequential-logic": EVALUATION_ROOT / "shidi-evaluation-review-20261027",
    "damage-memory": EVALUATION_ROOT / "shidi-damage-memory-runs",
}
RUNS = {
    "sequential-logic": EVALUATION_ROOT / "shidi-sequential-logic-runs",
    "damage-memory": EVALUATION_ROOT / "shidi-damage-memory-runs",
}
ARM_RUN = {
    "sequential-logic": {"pro": "b28eb4e-k28max-01/with", "flash": "6e03d72-k28max-01/with", "without": "b28eb4e-k28max-01/without"},
    "damage-memory": {"pro": "pro-b28", "flash": "flash-6e", "without": "without"},
}
CHAT_EVIDENCE = {
    "pro": ["保留原始设想并收敛为可证伪问题", "识别关键机制断点，不把组件当完整链条", "直接证据与类推分层，原始 PDF/DOI 可复核", "提出反例与可操作对照", "给出 1–2 条候选路线与优先级", "失败和未知透明，但有确认与耗时"],
    "flash": ["基本保留设想，个别机制表述过强", "整体机制合理但关键条件有遗漏", "全文覆盖较少，部分依赖摘要", "有对照但个别条件改变原题约束", "路线清楚但优先级论证较少", "无提问且较快，仍有证据边界"],
    "without": ["核心设想部分被强结论替代", "存在关键因果或顺序误判", "有 PDF 但关键来源解释存在矛盾", "对照定义正确但证据适用有误", "路线较宽，候选优先级不突出", "无提问，中心结论有时过强"],
}
KIMI_EVIDENCE = {
    "exploration": "覆盖相邻领域并保留核心问题",
    "evidence_reliability": "原文支持程度、阅读深度和数值一致性",
    "evidence_separation": "直接证据、类推证据与待验证设想的区分",
    "pdf_delivery": "实际 PDF 可打开、题名匹配与失败透明",
    "synthesis": "候选路线、交付物和下一步可执行性",
    "autonomy": "提问必要性、交互成本与预算执行",
    "topic_1": "主题核心机制是否准确保留",
    "topic_2": "关键时序/结构/功能证据是否成立",
    "distinction_failure": "普通机制与目标机制的区分及失效边界",
}
TOPIC_LABELS = {
    "sequential-logic": ("顺序逻辑", "状态保持"),
    "damage-memory": ("损伤记忆", "第二次修复加速"),
}


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def write_rubrics(case, content):
    weights = content["weights"]
    rows = []
    for key, weight in weights.items():
        row = {"dimension": key, "weight": weight}
        for arm in ("pro", "flash", "without"):
            values = content["arms"][arm].get("chatgpt", content["arms"][arm])
            row[arm] = values[key]
        rows.append(row)
    write_csv(BASE / case / "chatgpt-rubric.csv", ["dimension", "weight", "pro", "flash", "without"], rows)
    labels = {"question": "问题保真", "mechanism": "机制与因果", "evidence": "原始证据", "falsification": "证伪与对照", "synthesis": "综合路线", "autonomy": "透明与自主"}
    md = ["# ChatGPT 权重续评细则（非 ChatGPT 最终公开评分）", "", "| 维度 | 权重 | Pro | Flash | without |", "|---|---:|---:|---:|---:|"]
    md += [f"| {labels[r['dimension']]} | {r['weight']} | {r['pro']} | {r['flash']} | {r['without']} |" for r in rows]
    md += ["", "各维度均按原始分值计入；总分由程序加总。证据说明如下。", ""]
    for i, key in enumerate(weights, 1):
        md.append(f"## {labels[key]}")
        for arm in ("pro", "flash", "without"):
            md.append(f"- **{arm}**：{CHAT_EVIDENCE[arm][i-1]}")
        md.append("")
    (BASE / case / "chatgpt-rubric.md").write_text("\n".join(md), encoding="utf-8")


def write_kimi(case, content):
    rows = []
    for item in content["nine_dimensions"]:
        row = {"dimension": item["id"], "weight": item["weight"]}
        for arm in ("pro", "flash", "without"):
            row[arm] = item[arm]
        rows.append(row)
    write_csv(BASE / case / "kimi-rubric.csv", ["dimension", "weight", "pro", "flash", "without"], rows)
    md = ["# Kimi 评分细则与加总校验", "", "| 维度 | 权重 | Pro | Flash | without |", "|---|---:|---:|---:|---:|"]
    for row in rows:
        did = row["dimension"]
        if did.startswith("topic_"):
            index = int(did[-1]) - 1
            did = TOPIC_LABELS[case][index]
        md.append(f"| {did} | {row['weight']} | {row['pro']} | {row['flash']} | {row['without']} |")
    totals = {arm: round(sum(row[arm] for row in rows), 2) for arm in ("pro", "flash", "without")}
    md += ["", f"程序加总：Pro={totals['pro']}，Flash={totals['flash']}，without={totals['without']}。", "", "## 证据检查口径"]
    for did, text in KIMI_EVIDENCE.items():
        if not did.startswith("topic_"):
            md.append(f"- **{did}**：{text}")
    md += ["- **主题专属检查**：是否保留核心机制，是否将自增强/普通双响应/普通自修复误当成目标现象。", "- **失效边界**：是否明确不可达条件、反例和证伪方案。"]
    (BASE / case / "kimi-rubric.md").write_text("\n".join(md), encoding="utf-8")


def write_final(case, totals):
    rows = []
    for arm in ("pro", "flash", "without"):
        values = totals[arm]
        rows.append({"arm": arm, "chatgpt": values["chatgpt"], "kimi": values["kimi"], "aggregate": values["aggregate"]})
    write_csv(BASE / case / "final-scores.csv", ["arm", "chatgpt", "kimi", "aggregate"], rows)
    md = ["# 三大评分体系与最终得分", "", "| 条件 | ChatGPT 权重续评 | Kimi 修正评分 | 三大体系汇总 |", "|---|---:|---:|---:|"]
    md += [f"| {r['arm']} | {r['chatgpt']} | {r['kimi']} | {r['aggregate']} |" for r in rows]
    md += ["", "汇总轴由 ChatGPT 深度轴与对应 Kimi 归一化轴各取一半，其他轴沿用 ChatGPT 值，不是简单平均。", "以 ChatGPT 权重续评为主展示增益；三组同时呈现，避免只展示 Pro。"]
    (BASE / case / "final-scores.md").write_text("\n".join(md), encoding="utf-8")


def write_usage(case):
    rows = []
    for arm, relative in ARM_RUN[case].items():
        root = RUNS[case] / relative
        state = json.loads((root / "run.json").read_text(encoding="utf-8"))
        verify = json.loads((root / "output/pdf-verification.json").read_text(encoding="utf-8"))
        tokens = state["tokens"]
        rows.append({"arm": arm, "inputOther": tokens["inputOther"], "output": tokens["output"],
                     "cacheRead": tokens["inputCacheRead"], "cacheCreation": tokens["inputCacheCreation"],
                     "wall_seconds": state["wall_time_seconds_total"], "questions": state["coordinator_question_rounds"],
                     "pdf": verify["pdf_count"], "cost": state["cost"]})
    fields = ["arm", "inputOther", "output", "cacheRead", "cacheCreation", "wall_seconds", "questions", "pdf", "cost"]
    write_csv(BASE / case / "usage.csv", fields, rows)
    md = ["# 实际用量与交付", "", "| 组别 | inputOther | output | 缓存读取 | 缓存创建 | Agent 总墙钟(s) | 问答 | 核验 PDF | 人民币 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    md += [f"| {r['arm']} | {r['inputOther']} | {r['output']} | {r['cacheRead']} | {r['cacheCreation']} | {r['wall_seconds']} | {r['questions']} | {r['pdf']} | 无法核验 |" for r in rows]
    md += ["", "token/cache 为全部 usage.record 之和；墙钟取 Agent 工具回执，包含续跑。无逐次扣费字段，金额记 null，不用估价。"]
    (BASE / case / "usage.md").write_text("\n".join(md), encoding="utf-8")


for case, source in SOURCES.items():
    (BASE / case).mkdir(parents=True, exist_ok=True)
    content = json.loads((source / "computed-scores.json").read_text(encoding="utf-8"))
    if case == "sequential-logic":
        chat_content = json.loads((source / "scores.json").read_text(encoding="utf-8"))
        weights = chat_content["weights"]
        arms = chat_content["cases"]["sequential_logic"]["arms"]
    else:
        chat_content = json.loads((source / "depth-scores.json").read_text(encoding="utf-8"))
        weights = chat_content["weights"]
        arms = chat_content["arms"]
    write_rubrics(case, {"weights": weights, "arms": arms})
    kimi_content = (BASE / "kimi-sequential.json" if case == "sequential-logic" else source / "evaluation.json")
    write_kimi(case, json.loads(kimi_content.read_text(encoding="utf-8")))
    write_final(case, content["totals"][case.replace("-", "_")] if case == "sequential-logic" else content["totals"])
    write_usage(case)
    print(case, "4 tables written")
