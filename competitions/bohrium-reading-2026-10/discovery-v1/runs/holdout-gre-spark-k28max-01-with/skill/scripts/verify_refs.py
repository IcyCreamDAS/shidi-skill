#!/usr/bin/env python3
"""shidi 报告引用核验器 — 移植自 OpenAI4S literature-review/kernel.py (MIT)。

verify_dois: 逐条 DOI 核验（CrossRef API + doi.org HEAD fallback + 撤稿检测）。
style_pass:  确定性文风 lint（无 LLM，防间接注入）。
crossref_lookup: 自由文本引用 → DOI（不猜）。
extract_dois:    从文本抓全部 DOI。

原版经 host.web_fetch 走 OpenAI4S 内核；此处换 urllib.request（stdlib 零依赖），
HEAD 用 no-redirect handler 保持"origin 状态码"语义（302=注册、404=假 DOI）。

用法:
    python verify_refs.py report.md              # 抽 DOI 核验 + style_pass，输出 JSON
    python verify_refs.py --doi 10.xxxx --doi 10.yyyy
    python verify_refs.py --style-only report.md # 只跑文风 lint
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DOI_PATTERN = r"10\.\d{4,9}/[^\s\"'`\]\}—–&|]+"

UA = "shidi-verify-refs/1.0"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Don't follow redirects: doi.org 的 302 正是"DOI 已注册"的证据，
    跟随后拿到的是出版商 403 付费墙状态码，语义就坏了。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch(url: str, timeout: float = 15, head: bool = False) -> tuple[int, str | None]:
    """GET/HEAD 一次，返回 (status, body)。429 时 2s 后重试一次；
    网络错误返回 (0, None) —— 与 404 严格区分。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD" if head else "GET")
    for attempt in (0, 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, (None if head else r.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                time.sleep(2)
                continue
            return e.code, (None if head else "null")
        except Exception:
            return 0, None
    return 0, None


def litrev_get(url: str, timeout: float = 15) -> dict | None:
    status, body = _fetch(url, timeout)
    if status and 200 <= status < 300 and body:
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return None
    return None


def litrev_head(url: str, timeout: float = 10) -> int | None:
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
    for attempt in (0, 1):
        try:
            with opener.open(req, timeout=timeout) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                time.sleep(2)
                continue
            return e.code
        except Exception:
            return None
    return None


def quote_doi_path(doi: str) -> str:
    return "/".join(
        urllib.parse.quote(urllib.parse.unquote(seg), safe="") for seg in doi.split("/")
    )


def crossref_year(m: dict) -> int | None:
    dp = (m.get("published") or {}).get("date-parts") or [[None]]
    return (dp[0] or [None])[0]


def verify_dois(dois: list[str]) -> dict[str, dict]:
    """返回 {doi: {ok, title?, year?, journal?, retracted?, registry?, error?}}:
    ok=True 已解析; ok=False 未解析（doi.org 404，疑似编造/笔误）;
    ok=None 未能核验（网络/瞬时/5xx）——不得判为编造。"""
    out: dict[str, dict] = {}
    for d in dois:
        d = d.strip()
        segs = urllib.parse.unquote(d).split("/")
        if any(seg in ("", ".", "..") for seg in segs[1:]):
            out[d] = {"ok": False, "error": "dot-segment in DOI"}
            continue
        enc = quote_doi_path(d)
        j = litrev_get(f"https://api.crossref.org/works/{enc}")
        time.sleep(0.06)
        if j and "message" in j:
            m = j["message"]
            title = (m.get("title") or [""])[0]
            upd = [u.get("type", "") for u in (m.get("update-to") or [])]
            retracted = (
                any("retract" in t.lower() for t in upd)
                or str(m.get("subtype") or "").lower() == "retraction"
                or title.upper().startswith("RETRACTED")
            )
            out[d] = {
                "ok": True,
                "title": title,
                "year": crossref_year(m),
                "journal": (m.get("container-title") or [""])[0],
                "retracted": retracted,
                "registry": "crossref",
            }
            continue
        code = litrev_head(f"https://doi.org/{enc}")
        if code is not None and 200 <= code < 400:
            out[d] = {"ok": True, "registry": "non-crossref", "retracted": None}
        elif code == 404:
            out[d] = {"ok": False}
        else:
            out[d] = {"ok": None, "error": "unverified (network)", "retracted": None}
    return out


def crossref_lookup(ref_string: str) -> dict | None:
    """自由文本引用（作者/标题/年份）→ CrossRef 顶部匹配 {doi, title, year, score}。"""
    q = urllib.parse.quote(ref_string)
    j = litrev_get(f"https://api.crossref.org/works?query.bibliographic={q}&rows=1")
    items = (j or {}).get("message", {}).get("items", [])
    if not items:
        return None
    m = items[0]
    return {
        "doi": m.get("DOI"),
        "title": (m.get("title") or [""])[0],
        "year": crossref_year(m),
        "score": m.get("score"),
    }


def html_decode(s: str) -> str:
    for a, b in (
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&amp;", "&"),
        ("&nbsp;", " "),
        ("&#x2F;", "/"),
        ("&#47;", "/"),
    ):
        s = s.replace(a, b)
    return s


def extract_dois(text: str) -> list[str]:
    """从文本抓全部 DOI（HTML 实体解码、括号平衡、markdown/标点剥离）。"""
    decoded = html_decode(text)
    out: set[str] = set()
    for m in re.findall(DOI_PATTERN, decoded):
        d = m.split("</")[0]
        if d.count("<") != d.count(">"):
            d = d.split("<")[0]
        d = d.rstrip("_]*>`,;:")
        if d.endswith("."):
            d = d[:-1]
        while d.endswith(")") and d.count("(") < d.count(")"):
            d = d[:-1]
        if len(d) > 8:
            out.add(d)
    return sorted(out)


def style_pass(draft: str) -> dict:
    """确定性文风 lint。无 LLM by design：报告引用第三方文本，LLM 改写建议
    是间接注入通道；regex 代码是承重检查。"""
    issues: list[dict] = []
    w = len(draft.split()) or 1
    em = draft.count("—")
    if em > 6 and 1000 * em / w > 8:
        issues.append(
            {
                "code": "EMDASH",
                "note": f"{em} em-dashes ({1000*em/w:.0f}/1kw); replace most with comma/colon/period, keep at most one per paragraph",
            }
        )
    m = re.search(
        r"\b(the\s+|an?\s+)?honest(ly)?\s+(answer|summary|read|reading|look|perspective|assessment|appraisal|take|view)\b",
        draft,
        re.I,
    )
    if m:
        issues.append(
            {
                "code": "HONEST",
                "note": f"{m.group(0)!r}: drop the framing, write the sentence it was guarding",
            }
        )
    if re.search(
        r"(DOIs?\s+(were\s+)?verif|verified against (CrossRef|PubMed)|no retraction|current as of)",
        draft,
        re.I,
    ):
        issues.append(
            {"code": "PROCNOTE", "note": "process-narration line present; delete it"}
        )
    if re.search(r"\]\(https://doi\.org/[^)\s]*\([^)\s]*\)", draft):
        issues.append(
            {
                "code": "PARENDOI",
                "note": "DOI href contains literal ; URL-encode as %28 %29 so the markdown link survives simpler renderers",
            }
        )
    h2 = [ln for ln in draft.split("\n") if ln.startswith("## ")]
    long_h2 = [ln for ln in h2 if len(ln.split()) > 8]
    if len(long_h2) >= 2:
        issues.append(
            {
                "code": "LONGHEAD",
                "note": f"{len(long_h2)} headings read as sentences; shorten to <=6-word noun phrases",
            }
        )
    if len(h2) >= 7 and not any(ln.startswith("### ") for ln in draft.split("\n")):
        issues.append(
            {
                "code": "FLATSTRUCT",
                "note": f"{len(h2)} top-level sections, no subsections; group related ## under a parent and demote to ###",
            }
        )
    return {"ok": len(issues) == 0, "issues": issues}


def main(argv: list[str]) -> int:
    try:  # Windows GBK 控制台
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(prog="verify_refs", description=__doc__.split("\n\n")[0])
    ap.add_argument("file", nargs="?", help="报告文件（md/txt）：抽 DOI 核验 + style_pass")
    ap.add_argument("--doi", action="append", default=[], help="直接核验的 DOI（可重复）")
    ap.add_argument("--style-only", action="store_true", help="只跑 style_pass，不核验 DOI")
    args = ap.parse_args(argv)

    if args.file and not args.style_only:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
        dois = extract_dois(text)
        print(json.dumps({"verified_dois": verify_dois(dois), "style": style_pass(text)},
                         ensure_ascii=False, indent=2))
        return 0
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            print(json.dumps(style_pass(f.read()), ensure_ascii=False, indent=2))
        return 0
    if args.doi:
        print(json.dumps(verify_dois(args.doi), ensure_ascii=False, indent=2))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
