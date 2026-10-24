#!/usr/bin/env python3
"""Prepare matched transfer-case folders using the frozen unchanged Skill."""
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


def prepare(arm, out):
    if arm not in ("with", "without"):
        raise ValueError("arm must be with or without")
    lock = json.loads((BASE / "freeze.json").read_text())
    for name, expected in lock["files_sha256"].items():
        if digest(BASE / name) != expected:
            raise ValueError("Frozen transfer artifact changed: " + name)
    if hashes(REPO / "skills/shidi") != lock["skill_sha256"]:
        raise ValueError("Skill changed; this protocol requires the old unchanged version")
    out = Path(out).resolve()
    if out == REPO or REPO in out.parents or out in REPO.parents:
        raise ValueError("Run folder must be outside the repository and its ancestors")
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(BASE / "materials", out / "input")
    (out / "output").mkdir()
    for name in ("task.md", "criteria.md", "record_command.py"):
        shutil.copyfile(BASE / name, out / name)
    if arm == "with":
        shutil.copytree(REPO / "skills/shidi", out / "skill",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    common = ("仅读取本运行目录，结果写入output/；不要联网或读取其他目录、其他会话、评估答案。"
              "所有终端命令均用本目录record_command.py执行：把shell命令正文通过stdin传给它。"
              "记录器保留真实命令、stdout/stderr和退出码，不是完整会话导出。最多16次记录命令、15分钟墙钟、核心输出32 KiB。"
              "首条命令可读取PROMPT.md；完成后写output/run-notes.json，如实记录完成/中断、失败与未知信息，"
              "不猜测模型版本、token或费用。只读取input/内实际提供的材料，不声称看过缺失的图片。\n\n")
    extra = "使用本目录skill/SKILL.md中的Shidi及随附资源完成任务。\n\n" if arm == "with" else ""
    (out / "PROMPT.md").write_text(common + extra + (BASE / "task.md").read_text() + "\n" +
                                   (BASE / "criteria.md").read_text())
    state = {"status": "prepared-not-executed", "case": "transfer-v1", "arm": arm,
             "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
             "input_sha256": hashes(out / "input"), "task_sha256": digest(out / "task.md"),
             "criteria_sha256": digest(out / "criteria.md"),
             "recorder_sha256": digest(out / "record_command.py"),
             "skill_sha256": lock["skill_sha256"] if arm == "with" else None,
             "native_conversation_export": None, "model_settings": None, "cost": None}
    (out / "run.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return state


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=["with", "without"], required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    prepare(a.arm, a.out)
    print(json.dumps({"status": "prepared-not-executed", "out": str(a.out.resolve())}))
