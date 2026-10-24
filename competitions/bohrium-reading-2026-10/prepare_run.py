#!/usr/bin/env python3
"""Prepare isolated inputs. Does not call a model or manufacture a session trace."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent
REPO = BASE.parent.parent


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def prepare(case, arm, out):
    if case not in {"A", "B", "C"} or arm not in {"with", "without"}:
        raise ValueError("case must be A/B/C and arm must be with/without")
    out = Path(out).resolve()
    if out == REPO or REPO in out.parents:
        raise ValueError("Place run directories outside the repository to avoid exposing references")
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite an existing run: {out}")
    out.mkdir(parents=True)
    (out / "input").mkdir()
    (out / "output").mkdir()
    for path in (BASE / "materials" / case).iterdir():
        if path.is_file():
            shutil.copy2(path, out / "input" / path.name)
    task = (BASE / "cases" / case / "task.md").read_text(encoding="utf-8")
    criteria = (BASE / "cases" / case / "criteria.md").read_text(encoding="utf-8")
    shutil.copy2(BASE / "cases" / case / "task.md", out / "task.md")
    shutil.copy2(BASE / "cases" / case / "criteria.md", out / "criteria.md")
    extra = ""
    skill_hashes = None
    if arm == "with":
        shutil.copytree(REPO / "skills" / "shidi", out / "skill",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        skill_hashes = hashes(out / "skill")
        extra = "使用本目录 skill/SKILL.md 中的 shidi Skill 及其随附资源完成任务。\n\n"
    common = ("只读取本工作目录中的任务与输入，仅在 output/ 写入结果；不要读取其他目录、"
              "其他会话、评估参考或使用联网工具。可使用本地文件读取、XML/表格解析和计算工具。"
              "最多 12 次工具调用、15 分钟，核心输出总计不超过 24 KiB。直接完成任务。\n\n")
    (out / "PROMPT.md").write_text(common + extra + task + "\n" + criteria, encoding="utf-8")
    metadata = {
        "schema": "shidi-run-preparation/v1", "status": "prepared-not-executed",
        "case": case, "arm": arm, "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": hashes(out / "input"),
        "task_sha256": hashlib.sha256(task.encode()).hexdigest(),
        "criteria_sha256": hashlib.sha256(criteria.encode()).hexdigest(),
        "prompt_sha256": hashlib.sha256((out / "PROMPT.md").read_bytes()).hexdigest(),
        "skill_sha256": skill_hashes,
        "limits": {"tool_calls": 12, "wall_clock_minutes": 15, "output_bytes": 24576},
        "model": None, "model_settings": None, "cost": None,
        "actual_session_trace": None,
        "note": "Preparation only; record actual model/settings/usage and export the real session separately."
    }
    (out / "run.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=["A", "B", "C"])
    parser.add_argument("--arm", required=True, choices=["with", "without"])
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.case, args.arm, args.out)
    print(json.dumps({"out": str(args.out.resolve()), "status": result["status"],
                      "case": args.case, "arm": args.arm}, ensure_ascii=False))
