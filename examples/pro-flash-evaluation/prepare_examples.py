#!/usr/bin/env python3
"""Copy public-safe evaluation evidence without raw logs or unlicensed PDFs."""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EXTERNAL = Path(os.environ["SHIDI_EVALUATION_ROOT"])
BASE = REPO / "examples/pro-flash-evaluation"
CASES = {
    "sequential-logic": {
        "root": EXTERNAL / "shidi-sequential-logic-runs",
        "result": "COMPARISON.md",
        "protocol": "b28eb4e-k28max-01/PROTOCOL.md",
        "arms": {
            "pro": Path("b28eb4e-k28max-01/with"),
            "flash": Path("6e03d72-k28max-01/with"),
            "without": Path("b28eb4e-k28max-01/without"),
        },
    },
}
REPLACEMENTS = (
    (str(EXTERNAL / "shidi-sequential-logic-runs"), "<sequential-runs>"),
    (str(REPO), "<skill-repository>"),
    (str(EXTERNAL), "<workspace>"),
    (str(Path.home()), "<local-home>"),
)


def sanitize(text):
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def copy_text(source, target):
    text = sanitize(source.read_text(encoding="utf-8"))
    forbidden = ("610136", "060264", "PLAYGROUND_TOKEN", "access_key", "refresh_token")
    if any(item in text for item in forbidden):
        raise ValueError("Sensitive token-like content in " + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


for case, config in CASES.items():
    root = config["root"]
    destination = BASE / case
    for arm, relative in config["arms"].items():
        source = root / relative
        for name in ("task.md", "CONTEXT.md", "run.json", "visible_conversation.md", "trace-export.jsonl"):
            copy_text(source / name, destination / arm / name)
        for path in sorted((source / "output").rglob("*")):
            if path.is_file() and path.suffix.lower() in (".md", ".json", ".csv", ".txt"):
                copy_text(path, destination / arm / "output" / path.relative_to(source / "output"))
    copy_text(root / config["result"], destination / "RESULTS.md")
    copy_text(root / config.get("protocol", "PROTOCOL.md"), destination / "PROTOCOL.md")
    if (root / "CRITERIA.md").is_file():
        copy_text(root / "CRITERIA.md", destination / "CRITERIA.md")
    if (root / "evaluation.json").is_file():
        copy_text(root / "evaluation.json", destination / "evaluation.json")

print(f"Prepared {len(CASES)} case(s) × 3 arms; raw wire and PDF binaries excluded")
