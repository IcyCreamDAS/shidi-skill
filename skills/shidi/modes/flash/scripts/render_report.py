#!/usr/bin/env python3
"""shidi 多格式报告渲染器:Markdown -> HTML -> PDF。

用法:
    python render_report.py report.md                  # 出 HTML + PDF
    python render_report.py report.md --html-only      # 只出 HTML
    python render_report.py report.md --out dir/       # 指定输出目录

HTML 渲染依赖 markdown 包(pip install markdown)。PDF 通过本机已安装的
Edge / Chrome / Chromium headless 打印,跨平台自动探测(Windows / macOS / Linux);
也可用环境变量 SHIDI_BROWSER 指定浏览器可执行文件。
找不到浏览器时降级为只出 HTML 并提示。
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 平台默认安装路径(便携版/非标准安装请用 SHIDI_BROWSER 指定)
WINDOWS_BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]
MAC_BROWSERS = [
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
BROWSER_NAMES = (
    "msedge",
    "microsoft-edge",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
)

CSS = """
body { font-family: "Microsoft YaHei", "SimSun", "Segoe UI", sans-serif;
       max-width: 880px; margin: 2em auto; padding: 0 1.5em;
       line-height: 1.7; color: #1a1a1a; }
h1 { font-size: 1.6em; border-bottom: 2px solid #444; padding-bottom: .3em; }
h2 { font-size: 1.3em; border-bottom: 1px solid #ccc; padding-bottom: .2em; }
h3 { font-size: 1.1em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #bbb; padding: .4em .6em; font-size: .95em; }
th { background: #f0f0f0; }
code { background: #f5f5f5; padding: .15em .35em; border-radius: 3px;
       font-family: Consolas, monospace; font-size: .92em; }
pre { background: #f5f5f5; padding: .8em 1em; border-radius: 4px; overflow-x: auto; }
blockquote { border-left: 3px solid #999; margin-left: 0; padding-left: 1em; color: #555; }
a { color: #0645ad; }
@media print { body { max-width: 100%; margin: 0; } }
"""


def browser_candidates():
    """按优先级给出候选浏览器:SHIDI_BROWSER -> PATH 中的命令 -> 平台默认安装路径。"""
    override = os.environ.get("SHIDI_BROWSER", "").strip()
    if override:
        yield override
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            yield found
    for cand in WINDOWS_BROWSERS + MAC_BROWSERS:
        if Path(cand).exists():
            yield cand


def find_browser() -> str | None:
    for cand in browser_candidates():
        if Path(cand).exists() or shutil.which(cand):
            return cand
    return None


def md_to_html(md_text: str) -> str:
    try:
        import markdown
    except ImportError as exc:  # 渲染 HTML 的必需依赖,退化为报错而不是半成品
        raise RuntimeError("HTML 渲染需要 markdown 包: pip install markdown") from exc
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "toc"])
    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>"
    )


def html_to_pdf(browser: str, html_path: Path, pdf_path: Path) -> bool:
    # Edge 是 Windows 程序:必须传绝对 Windows 路径,相对路径/Git Bash 的
    # /tmp 风格路径解析会失败
    try:
        # Keep the previous report until this invocation produces a valid replacement.
        with tempfile.TemporaryDirectory(prefix=".shidi-render-", dir=pdf_path.resolve().parent) as folder:
            fresh = Path(folder) / pdf_path.name
            cmd = [
                browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--print-to-pdf=" + str(fresh),
                html_path.resolve().as_uri(),
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=90)
            if result.returncode == 0 and fresh.is_file() and fresh.stat().st_size > 1000:
                with fresh.open("rb") as handle:
                    valid = handle.read(5) == b"%PDF-"
                if valid:
                    fresh.replace(pdf_path)
                    return True
            print(f"! PDF 生成失败(浏览器输出: {result.stderr.decode(errors='ignore')[:200]})", file=sys.stderr)
            return False
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"! PDF 生成失败: {exc}", file=sys.stderr)
        return False


def main() -> int:
    # Windows 控制台默认 GBK,强制 UTF-8 保证中文/符号输出不崩
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("md", help="Markdown 报告路径")
    parser.add_argument("--out", default=None, help="输出目录(默认与 md 同目录)")
    parser.add_argument("--html-only", action="store_true", help="只生成 HTML")
    args = parser.parse_args()

    md_path = Path(args.md)
    if not md_path.exists():
        print(f"文件不存在: {md_path}", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else md_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        html = md_to_html(md_path.read_text(encoding="utf-8"))
    except RuntimeError as exc:
        print(f"! {exc}", file=sys.stderr)
        return 1
    html_path = out_dir / (md_path.stem + ".html")
    html_path.write_text(html, encoding="utf-8")
    print(f"✓ HTML: {html_path}")

    if args.html_only:
        return 0

    browser = find_browser()
    if not browser:
        print("! 未找到 Edge/Chrome,跳过 PDF(仅输出 HTML)。", file=sys.stderr)
        return 0
    pdf_path = out_dir / (md_path.stem + ".pdf")
    if html_to_pdf(browser, html_path, pdf_path):
        print(f"✓ PDF: {pdf_path}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
