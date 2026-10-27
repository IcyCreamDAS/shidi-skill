#!/usr/bin/env python3
"""Build the sequential-logic evidence package with pinned official tools."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
SKILL_VERSION = "git:b28eb4e"
SKILL_SHA256 = "51e04a4e853668e6619a824afcd9820531ea7ab267ceba944f9d54d5d65e0eed"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def effect_is_obvious(with_total, without_total, with_serious_errors=False):
    return with_total >= 75 and with_total - without_total >= 20 and not with_serious_errors


def safe_relative(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError("Unsafe relative path: " + name)
    if any(x in ("", ".", "..") for x in name.split("/")):
        raise ValueError("Non-canonical relative path: " + name)
    return p


def checked_file(root, name):
    safe_relative(name)
    p = root / name
    if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
        raise ValueError("Missing, linked or escaping source: " + name)
    return p


def copy_file(source, target):
    if source.is_symlink() or not source.is_file() or not source.stat().st_size:
        raise ValueError("Only nonempty regular files can be packaged: " + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def copy_tree(source, target):
    for p in sorted(source.rglob("*")):
        if p.is_symlink():
            raise ValueError("Symlinks cannot be packaged: " + str(p))
        if p.is_file():
            copy_file(p, target / p.relative_to(source))


def deterministic_zip(source, archive):
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source.rglob("*")):
            if p.is_symlink():
                raise ValueError("Symlinks cannot be archived")
            if p.is_file():
                rel = p.relative_to(source).as_posix()
                safe_relative(rel)
                if not p.stat().st_size:
                    raise ValueError("Empty artifact: " + rel)
                info = zipfile.ZipInfo("submission/" + rel, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes())


def source_selection(source, path, purpose, *, marker=None, start=0, chars=1800):
    text = checked_file(source, path).read_text(encoding="utf-8")
    if marker is not None:
        start = text.index(marker)
    end = min(len(text), start + chars)
    while len(text[start:end].encode("utf-8")) > 8 * 1024:
        end -= 1
    if not 0 <= start < end <= len(text):
        raise ValueError("Invalid source selection: " + path)
    return {"path": path, "start": start, "end": end, "purpose": purpose}


def verify_resources(resources):
    lock = read_json(REPO / "competitions/bohrium-reading-2026-10/official-resources-lock.json")
    for item in lock["files"]:
        p = checked_file(resources, item["path"])
        if p.stat().st_size != item["bytes"] or sha(p) != item["sha256"]:
            raise ValueError("Official resource hash/size mismatch: " + item["path"])
    return lock


def reserve_output(path):
    path = path.resolve()
    repo = REPO.resolve()
    if path == repo or path.is_relative_to(repo) or repo.is_relative_to(path):
        raise ValueError("Output must be outside the source repository and its ancestors")
    path.mkdir(parents=True, exist_ok=False)
    return path


def make_manifest(resources, run_root):
    m = read_json(resources / "templates/manifest-with-bonus.json")
    m["cases"] = [case for case in m["cases"] if case["id"] == "A"]
    m["skill_version"] = SKILL_VERSION
    m["environment"] = {
        "host": "Kimi Code Desktop；独立 coder 子代理，无跨会话记忆",
        "model": "kimi-code/kimi-for-coding（K2.8 Preview），默认 max；profile.bind 已核对",
        "model_version": "K2.8 Preview；服务端精确构建号无法取得",
        "tools": ["WebSearch", "FetchURL", "Bash", "Python", "pypdf"],
        "dependencies": ["Python 3", "pypdf", "matplotlib（仅评阅绘图）"],
        "budget": "每组12分钟软墙、24查询、40页面动作、8篇核心文献；软限非平台硬停止",
        "human_steps": "主代理 K3.1 Pro 冻结协议、按 ANSWERS.md 统一代答并独立评阅；未提供化学路线或论文答案",
        "isolation_limit": "独立目录和会话，禁止读取/利用宿主记忆；指令边界不是OS沙箱",
        "usage_unavailable_reason": "日志无逐次人民币扣费字段；cost=null，不填0或估价",
    }
    task_source = "用户本轮提供的合成研究探索提示；非实验数据"
    m["materials"] = []
    for name in ("task.md", "CONTEXT.md"):
        m["materials"].append({"path": f"materials/{name}", "case_ids": ["A"], "role": "input",
                               "source": task_source, "version": "2026-10-26 frozen",
                               "retrieved_at": "2026-10-26", "data_type": "一句话研究请求与最小共同背景",
                               "sharing_basis": "用户授权用于本次评测与参赛"})
    for case in m["cases"]:
        case.update(task_file="cases/A/task.md", acceptance_criteria_file="cases/A/criteria.md",
                    input_files=["materials/task.md", "materials/CONTEXT.md"], reference_files=[])
    m["runs"] = []
    for arm, rid in (("with", "A-with"), ("without", "A-without")):
        run = run_root / arm
        state = read_json(run / "run.json")
        notes = read_json(run / "output/run-notes.json")
        outputs = [f"runs/{rid}/output/{name}" for name in (
            "report.md" if arm == "with" else "先光照后遇湿_化学顺序门控报告.md",
            "literature-list.md" if arm == "with" else "references_文献清单.md",
            "run-notes.json", "pdf-verification.json")]
        m["runs"].append({
            "id": rid, "case_id": "A", "condition": "with_skill" if arm == "with" else "without_skill",
            "skill_version": SKILL_VERSION if arm == "with" else "none",
            "output_files": outputs, "primary_output_files": outputs,
            "trace_files": [f"runs/{rid}/trace-export.jsonl", f"runs/{rid}/run.json",
                            f"runs/{rid}/visible_conversation.md"],
            "started_at": notes.get("start_utc", notes.get("started_at")),
            "duration_seconds": state["wall_time_seconds_total"], "cost": None,
            "unavailable_metadata": "精确服务端构建号和人民币扣费无法取得",
            "human_steps": ([{"role": "coordinator-as-user", "record": "runs/A-with/visible_conversation.md",
                              "scope": "按冻结立场回答领域/数量/要求/角度；未给路线或论文"}] if arm == "with" else []),
            "result": state["status"],
            "trace_scope": "trace-export为完整可见文本与工具事件，不含宿主系统提示或隐藏推理；本机用户名和绝对路径已脱敏，原始wire留作者本地",
            "complete_conversation_available": True,
        })
    m["attempt_history"] = {"earlier_attempts": [], "raw_logs_available": True,
                            "reason": "本案例首次配对；所有问答、失败、重试均保留"}
    m["submission_readiness"] = {
        "status": "ready-for-local-official-validation", "ready_to_submit": True,
        "gaps": [],
        "limits": ["仅一组独立公平对照，不满足官方高增益档所需至少两组", "with超过12分钟软预算", "单主题不能证明稳定优势或成本节约"],
        "official_structure_pass_is_not_scientific_validation": True,
    }
    return m


def make_selections(source):
    rows = []
    def add(path, purpose, **kw): rows.append(source_selection(source, path, purpose, **kw))
    add("materials/task.md", "A一句话原始输入", chars=500)
    add("report.md", "九项评分、效果门槛、成本与限制", chars=4500)
    add("runs/A-with/output/report.md", "with对直接证据为零和顺序逻辑的界定", marker="## 0.", chars=2500)
    add("runs/A-with/output/report.md", "with明确保留先湿后光风险", marker="## 12.", chars=1800)
    add("runs/A-without/output/先光照后遇湿_化学顺序门控报告.md", "without将TiO₂列为直接证据的原文表述", marker="**（a）", chars=1800)
    add("runs/A-without/output/先光照后遇湿_化学顺序门控报告.md", "without综合结论与工程风险表述", marker="## 4.", chars=1200)
    add("runs/A-with/output/literature-list.md", "with核心文献与阅读深度", chars=1800)
    add("runs/A-without/output/references_文献清单.md", "without下载与未获全文清单", chars=1500)
    add("runs/A-with/output/pdf-verification.json", "with PDF原件、页数与SHA-256核验", chars=1500)
    add("runs/A-without/output/pdf-verification.json", "without PDF原件、页数与SHA-256核验", chars=1500)
    add("runs/A-with/output/run-notes.json", "with问答、查询、下载与超时记录", chars=2400)
    add("runs/A-without/output/run-notes.json", "without查询、下载与运行记录", chars=2000)
    add("runs/A-with/output/failures.md", "with真实失败", chars=1200)
    add("runs/A-without/output/失败清单.md", "without真实失败", chars=1200)
    add("runs/A-with/trace-export.jsonl", "with原始可见对话与工具轨迹开头", chars=1200)
    add("runs/A-without/trace-export.jsonl", "without原始可见对话与工具轨迹开头", chars=1200)
    add("evaluation.json", "九项分数及效果门槛机器可读数据", chars=1800)
    return rows


def run_official(resources, script, args, log):
    result = subprocess.run([sys.executable, "-X", "utf8", str(resources / script), *map(str, args)],
                            capture_output=True, text=True, encoding="utf-8", cwd=resources)
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise ValueError("Official tool failed; inspect: " + str(log))
    return json.loads(result.stdout)


def build(run_root, resources, output):
    run_root = run_root.resolve()
    resources = resources.resolve()
    evaluation = read_json(run_root / "evaluation.json")
    if not effect_is_obvious(evaluation["with_total"], evaluation["without_total"], evaluation["with_serious_errors"]):
        raise ValueError("Effect threshold not met; chart and submission package are not authorized")
    if sha(run_root / "with/skill/SKILL.md") != SKILL_SHA256:
        raise ValueError("Skill is not frozen b28eb4e")
    if (run_root / "with/task.md").read_bytes() != (run_root / "without/task.md").read_bytes():
        raise ValueError("Matched task differs")
    lock = verify_resources(resources)
    output = reserve_output(output)
    source = output / "submission"
    source.mkdir()
    copy_tree(run_root / "with/skill", source / "skill")
    for name in ("task.md", "CONTEXT.md"):
        copy_file(run_root / "with" / name, source / "materials" / name)
    copy_tree(BASE / "cases", source / "cases")
    for arm, rid in (("with", "A-with"), ("without", "A-without")):
        copy_tree(run_root / arm / "output", source / "runs" / rid / "output")
        for name in ("run.json", "visible_conversation.md", "trace-export.jsonl"):
            copy_file(run_root / arm / name, source / "runs" / rid / name)
    for name in ("PROTOCOL.md", "ANSWERS.md", "freeze.json", "evaluation.json", "RESULTS.md",
                 "scores-six.csv", "six-dimensions.png", "six-dimensions.svg", "make_radar.py", "export_visible.py"):
        copy_file(run_root / name, source / name)
    copy_file(run_root / "RESULTS.md", source / "report.md")
    copy_file(BASE / "SUBMISSION_README.md", source / "README.md")
    copy_file(REPO / "LICENSE", source / "LICENSE")
    copy_file(REPO / "THIRD_PARTY_NOTICES.md", source / "THIRD_PARTY_NOTICES.md")
    copy_file(REPO / "competitions/bohrium-reading-2026-10/official-resources-lock.json",
              source / "official-resources-lock.json")
    write_json(source / "manifest.json", make_manifest(resources, run_root))
    write_json(output / "selections.json", make_selections(source))
    original = output / "original-submission.zip"
    deterministic_zip(source, original)
    final = output / "deliverables/submission.zip"
    run_official(resources, "make_review.py", ["--archive", original, "--selections", output / "selections.json",
                                               "--out", final, "--track", "read"], output / "make-review-result.json")
    check = run_official(resources, "check_submission.py", ["--archive", final, "--track", "read"],
                         output / "official-check.json")
    status = {"status": "ready-to-submit-locally-validated", "ready_to_submit": True,
              "archive_sha256": sha(final), "archive_bytes": final.stat().st_size,
              "official_structure_check": check, "rules_version": lock["rules_version"],
              "limits": ["仅一组配对；官方高增益档需至少两组", "未上传，无Attempt ID或比赛成绩"],
              "submit_helper_run": False, "uploaded": False, "attempt_id": None, "score": None}
    write_json(output / "submission-status.json", status)
    return status


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--resources", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.run_root, args.resources, args.out), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "needs_revision", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
