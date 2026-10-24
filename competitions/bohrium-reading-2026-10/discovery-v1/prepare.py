#!/usr/bin/env python3
"""Prepare isolated discovery-case folders without running a model."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def prepare(case, arm, out, lock_name="freeze.json"):
    if arm not in ("with", "without"):
        raise ValueError("arm must be with or without")
    if lock_name not in ("freeze.json", "freeze-patched.json"):
        raise ValueError("Unknown freeze lock")
    task = BASE / "cases" / case / "task.md"
    if not task.is_file():
        raise ValueError("Unknown discovery case")
    lock = json.loads((BASE / lock_name).read_text(encoding="utf-8"))
    for name, expected in lock["files_sha256"].items():
        if digest(BASE / name) != expected:
            raise ValueError("Frozen discovery artifact changed: " + name)
    actual_skill = hashes(REPO / "skills/shidi")
    if actual_skill != lock["skill_sha256"]:
        raise ValueError("Skill does not match the selected freeze lock")
    out = Path(out).resolve()
    if out == REPO or REPO in out.parents or out in REPO.parents:
        raise ValueError("Run folder must be outside the repository and its ancestors")
    out.mkdir(parents=True, exist_ok=False)
    (out / "output").mkdir()
    shutil.copyfile(task, out / "task.md")
    if arm == "with":
        shutil.copytree(REPO / "skills/shidi", out / "skill",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    common = ("你是独立评测执行代理。不要读取其他目录、联网、调用工具或写文件。"
              "最多3个助手回合；本轮只形成简短研究任务说明和分批检索计划，不实际检索。\n\n")
    extra = ("按以下 Shidi 流程执行。\n\n"
             + (REPO / "skills/shidi/SKILL.md").read_text(encoding="utf-8") + "\n\n") if arm == "with" else ""
    prompt = common + extra + task.read_text(encoding="utf-8")
    (out / "PROMPT.md").write_text(prompt, encoding="utf-8")
    state = {"status": "prepared-not-executed", "case": case, "arm": arm,
             "freeze_lock": lock_name, "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
             "task_sha256": digest(out / "task.md"),
             "prompt_sha256": digest(out / "PROMPT.md"),
             "skill_sha256": actual_skill if arm == "with" else None,
             "native_conversation_export": False, "visible_conversation_copy": True,
             "required_model": "kimi-code/kimi-for-coding", "required_reasoning_effort": "max",
             "model": None, "reasoning_effort": None, "tokens": None,
             "cost": None, "cost_currency": "CNY", "cost_status": "not-executed"}
    (out / "run.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["dev-peek", "holdout-pd", "holdout-gre"], required=True)
    parser.add_argument("--arm", choices=["with", "without"], required=True)
    parser.add_argument("--lock", default="freeze.json", choices=["freeze.json", "freeze-patched.json"])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.case, args.arm, args.out, args.lock)
    print(json.dumps({"status": "prepared-not-executed", "out": str(args.out.resolve())}))
