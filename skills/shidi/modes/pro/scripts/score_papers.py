#!/usr/bin/env python3
"""shidi 文献评分器:把 LLM 给的维度分变成确定性结果。

LLM 只负责给每个维度的整数分;封顶、一票否决、总分、排序全部由本脚本算,
避免"让模型心算 35+20+15+10+10+10"这种不可靠的反模式。

输入 JSON(文件或 stdin;单个对象或数组,也接受 {"papers": [...]}):
    [
      {"id": "10.1021/acs.joc.0c01234",
       "dimensions": {"topic": 30, "method": 16, "data": 12,
                      "journal": 9, "network": 2, "application": 8, "archive": 6}}
    ]

用法:
    python score_papers.py scores.json                 # 默认 schema v2(七维)
    python score_papers.py scores.json --schema v1     # 旧六维(向后兼容)
    python score_papers.py scores.json --format md     # Markdown 表
    python score_papers.py scores.json --strict        # 超过上限直接报错(默认封顶+警告)
    python score_papers.py --self-test

退出码:0 成功;1 输入错误;2 用法错误。
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMAS = {
    # 2026-08 之前的六维口径,保留向后兼容
    "v1": {
        "topic": 35,
        "method": 20,
        "journal": 15,
        "network": 10,
        "application": 10,
        "archive": 10,
    },
    # 2026-10 起:新增"数据完备度",压低期刊声望与人脉权重
    "v2": {
        "topic": 30,
        "method": 20,
        "data": 15,
        "journal": 10,
        "network": 5,
        "application": 10,
        "archive": 10,
    },
}
DEFAULT_SCHEMA = "v2"
VETO_DIM = "topic"
VETO_BELOW = 10


def _papers(data) -> list:
    if isinstance(data, dict) and "papers" in data:
        data = data["papers"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("输入必须是 JSON 数组、单个对象,或 {\"papers\": [...]}")
    return data


def score_paper(item, weights: dict, strict: bool = False) -> dict:
    if not isinstance(item, dict):
        raise ValueError("每篇文献必须是 JSON 对象")
    paper_id = str(item.get("id") or item.get("doi") or "").strip()
    if not paper_id:
        raise ValueError("文献缺少 id/doi 字段")

    dimensions = item.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError(f"{paper_id}: 缺少 dimensions 对象")

    missing = sorted(set(weights) - set(dimensions))
    if missing:
        raise ValueError(f"{paper_id}: 缺少维度 {', '.join(missing)}")
    unknown = sorted(set(dimensions) - set(weights))
    if unknown:
        raise ValueError(
            f"{paper_id}: 未知维度 {', '.join(unknown)}"
            f"(当前 schema 维度: {', '.join(weights)})"
        )

    capped: dict = {}
    warnings: list = []
    raw: dict = {}
    for name, cap in weights.items():
        value = dimensions[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{paper_id}: {name} 不是数字: {value!r}")
        if float(value) != int(value):
            raise ValueError(f"{paper_id}: {name} 必须是整数分,收到 {value!r}")
        value = int(value)
        raw[name] = value
        if value < 0:
            raise ValueError(f"{paper_id}: {name} 不能为负: {value}")
        if value > cap:
            message = f"{paper_id}: {name}={value} 超过上限 {cap}"
            if strict:
                raise ValueError(message)
            warnings.append(message + ",已封顶")
            value = cap
        capped[name] = value

    total = sum(capped.values())
    vetoed = capped[VETO_DIM] < VETO_BELOW
    return {
        "id": paper_id,
        "dimensions": capped,
        "raw_dimensions": raw,
        "total": total,
        "vetoed": vetoed,
        "rank": None,
        "warnings": warnings,
    }


def score_all(data, schema: str = DEFAULT_SCHEMA, strict: bool = False) -> dict:
    if schema not in SCHEMAS:
        raise ValueError(f"未知 schema: {schema}(可选: {', '.join(SCHEMAS)})")
    weights = SCHEMAS[schema]
    if sum(weights.values()) != 100:
        raise ValueError(f"schema {schema} 权重之和不是 100: {sum(weights.values())}")

    papers = [score_paper(item, weights, strict) for item in _papers(data)]
    seen = set()
    for paper in papers:
        if paper["id"] in seen:
            raise ValueError(f"重复文献 id: {paper['id']}; 请先去重后重试")
        seen.add(paper["id"])
    ranked = sorted((p for p in papers if not p["vetoed"]), key=lambda p: (-p["total"], p["id"]))
    for index, paper in enumerate(ranked, start=1):
        paper["rank"] = index

    warnings = [warning for paper in papers for warning in paper["warnings"]]
    return {
        "schema": schema,
        "weights": weights,
        "veto_rule": f"{VETO_DIM} < {VETO_BELOW}",
        "papers": papers,
        "ranking": [paper["id"] for paper in ranked],
        "vetoed": [paper["id"] for paper in papers if paper["vetoed"]],
        "warnings": warnings,
    }


def format_markdown(result: dict) -> str:
    dims = list(result["weights"])
    header = ["rank", "id", *dims, "total", "note"]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    ordered = sorted((paper for paper in result["papers"] if not paper["vetoed"]), key=lambda paper: paper["rank"])
    ordered += [paper for paper in result["papers"] if paper["vetoed"]]
    for paper in ordered:
        note = "vetoed (topic < 10)" if paper["vetoed"] else ""
        row = [str(paper["rank"] or "-"), paper["id"]]
        row += [str(paper["dimensions"][name]) for name in dims]
        row += [str(paper["total"]), note]
        lines.append("| " + " | ".join(row) + " |")
    if result["vetoed"]:
        lines.append("")
        lines.append(f"Vetoed: {', '.join(result['vetoed'])} (topic < {VETO_BELOW})")
    return "\n".join(lines)


def self_test() -> int:
    # 封顶:topic 36 -> 35
    result = score_all(
        [{"id": "a", "dimensions": {"topic": 36, "method": 20, "journal": 15,
                                    "network": 10, "application": 10, "archive": 10}}],
        schema="v1",
    )
    assert result["papers"][0]["dimensions"]["topic"] == 35, result
    assert result["papers"][0]["total"] == 100, result
    assert result["papers"][0]["rank"] == 1

    # 一票否决:topic 9
    vetoed = score_all(
        [{"id": "b", "dimensions": {"topic": 9, "method": 20, "journal": 15,
                                    "network": 10, "application": 10, "archive": 10}}],
        schema="v1",
    )
    assert vetoed["papers"][0]["vetoed"] is True
    assert vetoed["ranking"] == [] and vetoed["vetoed"] == ["b"]

    # v2 权重和 = 100
    assert sum(SCHEMAS["v2"].values()) == 100

    # 缺维度/未知维度/超上限 strict 都要报错
    for bad, kwargs in (
        ({"id": "c", "dimensions": {"topic": 30}}, {}),
        ({"id": "c", "dimensions": {"topic": 30, "method": 20, "data": 15, "journal": 10,
                                    "network": 5, "application": 10, "archive": 10, "noise": 1}}, {}),
        ({"id": "c", "dimensions": {"topic": 31, "method": 20, "data": 15, "journal": 10,
                                    "network": 5, "application": 10, "archive": 10}}, {"strict": True}),
    ):
        try:
            score_all([bad], schema="v2", **kwargs)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad} {kwargs}")

    print("SELF-TEST OK")
    return 0


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(prog="score_papers", description="确定性文献评分器")
    parser.add_argument("input", nargs="?", help="分数字 JSON 文件路径(缺省读 stdin)")
    parser.add_argument("--schema", choices=sorted(SCHEMAS), default=DEFAULT_SCHEMA)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--strict", action="store_true", help="超过维度上限直接报错(默认封顶并警告)")
    parser.add_argument("--self-test", action="store_true", help="运行内置自检")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.input:
        with open(args.input, encoding="utf-8") as handle:
            data = json.load(handle)
    else:
        data = json.load(sys.stdin)

    try:
        result = score_all(data, schema=args.schema, strict=args.strict)
    except ValueError as exc:
        print(f"评分失败: {exc}", file=sys.stderr)
        return 1

    if args.format == "md":
        print(format_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
