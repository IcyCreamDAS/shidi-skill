#!/usr/bin/env python3
"""Self-check for the shidi-skill repository (standard library only).

Run locally:   python validate.py
Runs in CI:    .github/workflows/ci.yml

Exit code 0 means every check passed. The checks exist so that the failure
modes that bit us once (unquoted YAML colons, version drift between
package.json / README badges, scripts that do not compile) are caught
before a maintainer has to catch them in review.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
failures: list[str] = []
checks = 0


def check(cond: bool, label: str, detail: str = "") -> bool:
    global checks
    checks += 1
    if cond:
        print(f"[ ok ] {label}")
        return True
    failures.append(f"{label}{(': ' + detail) if detail else ''}")
    print(f"[FAIL] {label}" + (f" - {detail}" if detail else ""))
    return False


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


# -- 1. package.json -------------------------------------------------------
pkg = {}
try:
    pkg = json.loads(read_text("package.json"))
    check(True, "package.json parses")
except Exception as exc:  # noqa: BLE001 - report and keep checking
    check(False, "package.json parses", str(exc))

version = str(pkg.get("version", ""))
check(bool(pkg.get("name")), "package.json has a name")
check(bool(version), "package.json has a version")
check(
    isinstance(pkg.get("dsh", {}).get("bundle", {}).get("patch"), str),
    "package.json declares dsh.bundle.patch",
)

# -- 2. version badges stay in sync ---------------------------------------
for readme in ("README.md", "README_EN.md"):
    try:
        badge = re.search(r"badge/version-([0-9][0-9.]*)", read_text(readme))
        check(
            badge is not None and badge.group(1) == version,
            f"{readme} version badge matches package.json",
            f"badge={badge.group(1) if badge else 'missing'} version={version}",
        )
    except FileNotFoundError:
        check(False, f"{readme} exists")

# -- 3. DSH bundle patch ---------------------------------------------------
try:
    patch = read_text("cordis.patch.yml")
    first = next(line for line in patch.splitlines() if line.strip())
    check(first.strip() == "- insert:", "cordis.patch.yml starts with '- insert:'", first.strip())
    check("shidi-dsh-plugin" in patch, "cordis.patch.yml references shidi-dsh-plugin")
    check("'@deepseek-ai/cordis-plugin-group'" in patch, "cordis.patch.yml mounts the skills group plugin")
except FileNotFoundError:
    check(False, "cordis.patch.yml exists")

# -- 4. SKILL.md frontmatter ----------------------------------------------
try:
    skill = read_text("skills/shidi/SKILL.md")
    lines = skill.splitlines()
    check(bool(lines) and lines[0].strip() == "---", "SKILL.md starts with YAML frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    check(end is not None, "SKILL.md frontmatter is closed")
    front = "\n".join(lines[1:end]) if end else ""
    check(re.search(r"(?m)^name:\s*\S+", front) is not None, "SKILL.md frontmatter has name")
    check(re.search(r"(?m)^description:\s*\S+", front) is not None, "SKILL.md frontmatter has description")
except FileNotFoundError:
    check(False, "skills/shidi/SKILL.md exists")

# -- 5. Python sources compile --------------------------------------------
py_files = sorted((ROOT / "skills").rglob("*.py"))
if (ROOT / "examples").is_dir():
    py_files += sorted((ROOT / "examples").rglob("*.py"))
check(bool(py_files), "Python scripts found")
for path in py_files:
    rel = path.relative_to(ROOT).as_posix()
    try:
        compile(path.read_text(encoding="utf-8"), rel, "exec")
        check(True, f"{rel} compiles")
    except SyntaxError as exc:
        check(False, f"{rel} compiles", str(exc))

# -- 6. JS entrypoints ----------------------------------------------------
for entry in ("index.mjs", "skills.mjs"):
    check((ROOT / entry).is_file() and (ROOT / entry).stat().st_size > 0, f"{entry} exists")

# -- 7. README relative links / images resolve ----------------------------
def markdown_local_targets(text: str) -> list[str]:
    targets: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("\x60\x60\x60"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        targets += re.findall(r"!?\[[^\]]*\]\(([^)\s]+)\)", line)
        targets += re.findall(r"<img[^>]*src=\"([^\"]+)\"", line)
    return targets


for readme in ("README.md", "README_EN.md"):
    try:
        text = read_text(readme)
    except FileNotFoundError:
        continue
    local = []
    for target in markdown_local_targets(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        local.append(target.split("#", 1)[0].split("?", 1)[0])
    missing = sorted({t for t in local if t and not (ROOT / t).exists()})
    check(not missing, f"{readme} relative links resolve", ", ".join(missing))

# -- 8. Example keeps its entrypoint contract ----------------------------
example = ROOT / "examples" / "materials_small_data"
if example.is_dir():
    for name in ("run_demo.py", "make_synthetic_data.py", "requirements.txt", "README.md"):
        check((example / name).is_file(), f"examples/materials_small_data/{name} exists")

# -- summary --------------------------------------------------------------
print()
if failures:
    print(f"FAILED: {len(failures)} of {checks} checks")
    for item in failures:
        print(f"  - {item}")
    sys.exit(1)

print(f"VALIDATION OK: {checks} checks passed")
