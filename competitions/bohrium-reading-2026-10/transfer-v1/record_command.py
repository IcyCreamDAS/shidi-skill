#!/usr/bin/env python3
"""Record real shell inputs/results. This is not a native model conversation export."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MAX_CALLS = 16
MAX_WALL = 900


def stamp():
    return datetime.now(timezone.utc).isoformat()


def execute(root, command):
    if not command.strip():
        raise ValueError("No command supplied on stdin")
    output = root / "output"
    output.mkdir(exist_ok=True)
    log = output / "commands.jsonl"
    previous = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    starts = [row for row in previous if row.get("event") == "command_started"]
    now = time.time()
    remaining = MAX_WALL - (now - starts[0]["epoch_seconds"]) if starts else MAX_WALL
    if len(starts) >= MAX_CALLS or remaining <= 0:
        raise ValueError("Recorded command budget exhausted; retain partial outputs")
    number = len(starts) + 1
    def append(value):
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False) + "\n")
    append({"event": "command_started", "id": number, "time_utc": stamp(),
            "epoch_seconds": now, "cwd": str(root), "command": command,
            "native_model_telemetry": False})
    begin = time.monotonic()
    timed_out = False
    try:
        completed = subprocess.run(["bash", "-euo", "pipefail", "-c", command], cwd=root,
                                   capture_output=True, text=True, encoding="utf-8", errors="replace",
                                   timeout=min(180, remaining))
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        code = 124
        decode = lambda s: s.decode("utf-8", errors="replace") if isinstance(s, bytes) else s or ""
        stdout, stderr = decode(error.stdout), decode(error.stderr)
    append({"event": "command_finished", "id": number, "time_utc": stamp(),
            "duration_seconds": time.monotonic() - begin, "returncode": code,
            "timed_out": timed_out, "stdout": stdout, "stderr": stderr})
    return code, stdout, stderr


if __name__ == "__main__":
    try:
        code, stdout, stderr = execute(ROOT, sys.stdin.read())
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        raise SystemExit(code)
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
