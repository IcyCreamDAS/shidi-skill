#!/usr/bin/env python3
"""Export visible Kimi wire events, excluding host prompts and private reasoning."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

URL = re.compile(r'https?://[^\s<>"\\]+', re.IGNORECASE)
AUTH_KEYS = re.compile(r'(?:[?&])(?:idnf|login_hint|access_token|refresh_token|id_token|oauth_token|code)=', re.IGNORECASE)


def redact_auth_urls(value):
    """Remove login redirects, including encoded account hints in nested tool text."""
    if isinstance(value, dict):
        return {k: redact_auth_urls(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_auth_urls(v) for v in value]
    if not isinstance(value, str):
        return value
    def replace(match):
        raw = match.group()
        decoded = raw
        for _ in range(3):
            decoded = unquote(decoded)
        host = urlsplit(decoded).hostname or ""
        if host == "accounts.google.com" or AUTH_KEYS.search(decoded):
            return "[REDACTED_AUTH_URL]"
        return raw
    return URL.sub(replace, value)


def export(source, destination):
    count = 0
    with source.open(encoding="utf-8") as src, destination.open("x", encoding="utf-8") as out:
        for line in src:
            row = json.loads(line)
            record = None
            if row.get("type") == "context.append_message" and row["message"].get("role") == "user":
                record = {"type": "user.message", "time": row.get("time"), "content": row["message"].get("content", [])}
            elif row.get("type") == "context.append_loop_event":
                event = row["event"]
                kind = event.get("type")
                if kind == "content.part" and event.get("part", {}).get("type") == "text":
                    record = {"type": "assistant.text", "time": row.get("time"), "text": event["part"].get("text", "")}
                elif kind == "tool.call":
                    record = {"type": kind, "time": row.get("time"), "toolCallId": event.get("toolCallId"),
                              "name": event.get("name"), "args": event.get("args", {})}
                elif kind == "tool.result":
                    record = {"type": kind, "time": row.get("time"), "toolCallId": event.get("toolCallId"),
                              "result": event.get("result", {})}
            if record is not None:
                out.write(json.dumps(redact_auth_urls(record), ensure_ascii=False) + "\n")
                count += 1
    return {"records": count, "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "scope": "visible user/assistant text and tools; no host prompts or private reasoning; auth redirects redacted"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.source, args.destination), ensure_ascii=False))
