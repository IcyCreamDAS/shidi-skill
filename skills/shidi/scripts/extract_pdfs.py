#!/usr/bin/env python3
"""shidi 文献 PDF 抽取层:pdf-inspector 分类 + 文本型转 Markdown。

用法:
    python extract_pdfs.py <PDF文件或目录> [--out 输出目录] [--force]

输出(每个 PDF 一个,与源同名):
    <name>.md         文本型 PDF 的干净 Markdown(阅读顺序/表格/标题已结构化)
    <name>.meta.json  分类:pdf_type + confidence + needs_vision + 统计

路由规则(精读阶段据此选择读法):
    text_based  -> 抽取 Markdown,精读读 .md 而非 .pdf(省上下文、表格不乱)
    scanned/image_based -> 不抽取,needs_vision=true,走视觉路径(Read/GLM)
    mixed       -> 抽取 Markdown(能抽多少是多少),needs_vision=true 补图

注意:化学论文的结构式/谱图是图像,文本抽取必丢,视觉层照走,两层互补。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# pdf-inspector 的 pdf_type 取值(process_pdf_bytes 返回 PdfResult)
TEXT_TYPES = ("text_based", "textbased")
VISION_TYPES = ("scanned", "image_based", "imagebased")
MIXED_TYPES = ("mixed",)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError, ValueError):
                pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="PDF 文件或包含 PDF 的目录")
    parser.add_argument("--out", default=None, help="输出目录(默认:目标旁 _md/)")
    parser.add_argument("--force", action="store_true", help="已存在也重新抽取")
    args = parser.parse_args()

    try:
        import pdf_inspector as pi
    except ImportError:
        print("缺少 pdf-inspector,请先: pip install pdf-inspector", file=sys.stderr)
        return 1

    target = Path(args.target)
    pdfs = [target] if target.is_file() else sorted(target.rglob("*.pdf"))
    if not pdfs:
        print(f"未找到 PDF: {target}", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else (target.parent if target.is_file() else target) / "_md"
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"text": 0, "vision": 0, "mixed": 0, "skip": 0, "fail": 0}
    for pdf in pdfs:
        meta_path = out_dir / f"{pdf.stem}.meta.json"
        if not args.force and meta_path.exists():
            stats["skip"] += 1
            print(f"  跳过(已存在): {pdf.name}")
            continue

        try:
            data = pdf.read_bytes()
            res = pi.process_pdf_bytes(data)  # PdfResult: pdf_type/confidence/markdown/pages_needing_ocr/...
            ptype = str(res.pdf_type or "").lower()

            if ptype in TEXT_TYPES:
                kind = "text_based"
            elif ptype in VISION_TYPES:
                kind = "vision"
            else:
                kind = "mixed"

            markdown = res.markdown or ""
            needs_ocr_pages = list(res.pages_needing_ocr or [])
            needs_vision = kind != "text_based" or bool(needs_ocr_pages)

            md_path = out_dir / f"{pdf.stem}.md"
            if markdown:
                md_path.write_text(markdown, encoding="utf-8")
            meta = {
                "source": pdf.name,
                "pdf_type": ptype,
                "confidence": res.confidence,
                "needs_vision": needs_vision,
                "markdown_written": bool(markdown),
                "pages_needing_ocr": needs_ocr_pages,
                "pages_with_tables": list(res.pages_with_tables or []),
                "has_encoding_issues": bool(res.has_encoding_issues),
                "processing_time_ms": res.processing_time_ms,
            }
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

            if kind == "text_based":
                stats["text"] += 1
                flag = f"✓ 文本型 → {md_path.name} ({len(markdown)} 字符)"
            elif kind == "vision":
                stats["vision"] += 1
                flag = "⛺ 扫描型 → 走视觉路径"
            else:
                stats["mixed"] += 1
                flag = "◐ 混合型 → 抽取 + 视觉补图"
            if needs_ocr_pages:
                flag += f" [部分页需 OCR: {needs_ocr_pages}]"
            print(f"  {flag}  [{pdf.name}] conf={res.confidence:.2f} {res.processing_time_ms}ms")
        except Exception as exc:
            stats["fail"] += 1
            print(f"  ✗ 失败 {pdf.name}: {type(exc).__name__}: {exc}", file=sys.stderr)

    print(f"\n完成: 文本型 {stats['text']} / 视觉型 {stats['vision']} / 混合 {stats['mixed']}"
          f" / 跳过 {stats['skip']} / 失败 {stats['fail']} → {out_dir}")
    return 0 if stats["fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
