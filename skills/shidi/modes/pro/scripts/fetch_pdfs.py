#!/usr/bin/env python3
"""shidi 文献 PDF 批量下载器。

输入 DOI 列表(或 OpenAlex 可解析的 URL),通过 OpenAlex / Unpaywall
查找开放获取(OA)PDF 链接并下载到指定目录。

用法:
    python fetch_pdfs.py --dois "10.1021/xxx,10.1002/yyy"
    python fetch_pdfs.py --input dois.txt --out assets/pdfs
    python fetch_pdfs.py --input dois.txt --out assets/pdfs --keep-going

输入文件格式:每行一个 DOI(或 https://doi.org/xxx 链接)。
下载成功的文件命名:<编号>_<DOI后段>.pdf,失败条目输出到 stderr。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT = 30
USER_AGENT = "shidi-literature-fetcher (research use)"
RETRYABLE_STATUS = (429, 500, 502, 503, 504)
DEFAULT_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "").strip()


def backoff_seconds(attempt: int, retry_after: str | None = None) -> float:
    """第 attempt 次重试(0-based)前的等待秒数:Retry-After 优先,否则指数退避。"""
    if retry_after:
        try:
            return max(0.0, min(float(retry_after), 60.0))
        except ValueError:
            pass
    return min(2.0 ** attempt, 8.0)


def doi_from_text(text: str) -> str:
    """从文本中提取 DOI(优先完整 doi.org 链接,否则裸 DOI)。"""
    text = text.strip()
    m = re.search(r"10\.\d{4,9}/[A-Za-z0-9._()\[\]:/-]+", text)
    if not m:
        return ""
    doi = m.group(0).rstrip(".,);")
    return urllib.parse.unquote(doi)


def http_get(
    url: str,
    headers: dict | None = None,
    retries: int = 3,
    opener=None,
    sleep=time.sleep,
) -> bytes | None:
    """带指数退避的 GET。429/5xx 重试(尊重 Retry-After),网络错误同样退避;

    opener/sleep 可注入,便于离线单测。
    """
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    open_ = opener or urllib.request.urlopen
    for attempt in range(retries + 1):
        try:
            with open_(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in RETRYABLE_STATUS and attempt < retries:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                sleep(backoff_seconds(attempt, retry_after))
                continue
            print(f"  ! 请求失败 {url}: HTTP {exc.code}", file=sys.stderr)
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt < retries:
                sleep(backoff_seconds(attempt))
                continue
            print(f"  ! 请求失败 {url}: {exc}", file=sys.stderr)
            return None
    return None


def find_oa_pdf(doi: str, email: str = "") -> str:
    """OpenAlex 优先,Unpaywall 兜底,返回 OA PDF URL(找不到返回空)。

    pdf_url 缺失时扫描所有 locations 里的 pdf_url(green OA 常见)。
    Unpaywall 需要邮箱;未提供时跳过(OpenAlex 不需要)。
    """
    # 1. OpenAlex(无 key,公开)
    data = http_get(f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}")
    if data:
        try:
            import json
            work = json.loads(data)
            loc = work.get("best_oa_location") or {}
            pdf_url = loc.get("pdf_url") or ""
            if not pdf_url:
                for item in work.get("locations") or []:
                    pdf_url = (item or {}).get("pdf_url") or ""
                    if pdf_url:
                        break
            if pdf_url:
                return pdf_url
        except Exception:
            pass
    # 2. Unpaywall(无 key,需邮箱;未配置则跳过)
    if not email:
        return ""
    time.sleep(0.5)  # 礼貌限速
    data = http_get(
        f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}"
    )
    if data:
        try:
            import json
            info = json.loads(data)
            loc = info.get("best_oa_location") or {}
            pdf_url = loc.get("url_for_pdf") or ""
            if pdf_url:
                return pdf_url
        except Exception:
            pass
    return ""


def looks_like_pdf(data: bytes | None) -> bool:
    """内容以 %PDF 开头(允许前导空白/UTF-8 BOM)。"""
    return bool(data) and data[:8].lstrip().startswith(b"%PDF")


def download_pdf(url: str, dest: Path) -> bool:
    """下载 PDF 到 dest,校验内容以 PDF 开头。"""
    data = http_get(url, headers={"Accept": "application/pdf"})
    if data is None:
        return False
    if not looks_like_pdf(data):
        print(f"  ! 不是 PDF 内容(可能是 HTML 登录页): {url}", file=sys.stderr)
        return False
    dest.write_bytes(data)
    return True


def main() -> int:
    # Windows 控制台默认 GBK,强制 UTF-8 保证中文/符号输出不崩
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dois", help="逗号分隔的 DOI 列表")
    parser.add_argument("--input", help="每行一个 DOI 的文本文件")
    parser.add_argument("--out", default="assets/pdfs", help="输出目录(默认 assets/pdfs)")
    parser.add_argument("--keep-going", action="store_true", help="个别失败不中断")
    parser.add_argument(
        "--email",
        default=DEFAULT_EMAIL,
        help="Unpaywall 联系邮箱(默认读取环境变量 UNPAYWALL_EMAIL;未设置则跳过 Unpaywall)",
    )
    args = parser.parse_args()

    email = (args.email or "").strip()
    if not email:
        print(
            "提示: 未设置 UNPAYWALL_EMAIL / --email,Unpaywall 兜底已跳过(OpenAlex 仍可用)。"
            " 设置环境变量 UNPAYWALL_EMAIL=your@email 可启用。",
            file=sys.stderr,
        )

    dois: list[str] = []
    if args.dois:
        dois = [doi_from_text(d) for d in args.dois.split(",")]
    elif args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"输入文件不存在: {path}", file=sys.stderr)
            return 1
        dois = [doi_from_text(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        parser.error("必须提供 --dois 或 --input")

    dois = [d for d in dois if d]
    if not dois:
        print("未解析到任何有效 DOI", file=sys.stderr)
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ok, fail = 0, 0
    for idx, doi in enumerate(dois, start=1):
        print(f"[{idx}/{len(dois)}] {doi}", file=sys.stderr)
        pdf_url = find_oa_pdf(doi, email)
        if not pdf_url:
            print(f"  ✗ 无 OA PDF(付费墙或未收录): {doi}", file=sys.stderr)
            fail += 1
            continue
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", doi)[:60]
        dest = out_dir / f"{idx:02d}_{safe}.pdf"
        if dest.exists():
            print(f"  ✓ 已存在,跳过: {dest.name}")
            ok += 1
            continue
        if download_pdf(pdf_url, dest):
            print(f"  ✓ {dest.name} <- {pdf_url}")
            ok += 1
        else:
            fail += 1
            if not args.keep_going:
                print("下载失败,中止(加 --keep-going 可继续)。", file=sys.stderr)
                return 1

    print(f"\n完成: 成功 {ok} / 失败 {fail},目录 {out_dir}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
