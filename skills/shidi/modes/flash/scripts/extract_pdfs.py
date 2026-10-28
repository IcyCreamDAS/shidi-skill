#!/usr/bin/env python3
"""shidi 文献 PDF 抽取层:pdf-inspector 分类 + 文本型转 Markdown。

用法:
    python extract_pdfs.py <PDF文件或目录> [--out 输出目录] [--force]

输出(每个 PDF 一个,与源同名):
    <name>.md         文本型 PDF 的干净 Markdown(阅读顺序/表格/标题已结构化)
    <name>.meta.json  分类:pdf_type + confidence + needs_vision + 统计

目录输入保留相对子目录,防止同名 PDF 冲突。缓存按源文件 SHA-256 核对;
旧缓存没有源哈希时会重新抽取,缺少 Markdown 时同样重建。
共享输出目录由另一输入占用时拒绝覆盖;请另选 --out 或明确加 --force。

路由规则(精读阶段据此选择读法):
    text_based  -> 抽取 Markdown,精读读 .md 而非 .pdf(省上下文、表格不乱)
    scanned/image_based -> 不抽取,needs_vision=true,走视觉路径(Read/GLM)
    mixed       -> 抽取 Markdown(能抽多少是多少),needs_vision=true 补图

注意:化学论文的结构式/谱图是图像,文本抽取必丢,视觉层照走,两层互补。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# pdf-inspector 的 pdf_type 取值(process_pdf_bytes 返回 PdfResult)
TEXT_TYPES = ("text_based", "textbased")
VISION_TYPES = ("scanned", "image_based", "imagebased")
MIXED_TYPES = ("mixed",)

# 对外契约:meta.json 的 kind 字段(与 SKILL.md 的路由规则一一对应)
KIND_TEXT = "text_based"
KIND_VISION = "vision"
KIND_MIXED = "mixed"


def classify(pdf_type: str | None) -> str:
    """把 pdf-inspector 的 pdf_type 映射为稳定的 kind 契约。

    text_based/textbased -> text_based(读 .md)
    scanned/image_based/imagebased -> vision(走视觉路径)
    其余(含 mixed/空值) -> mixed(.md + 视觉补图)
    """
    ptype = str(pdf_type or "").strip().lower()
    if ptype in TEXT_TYPES:
        return KIND_TEXT
    if ptype in VISION_TYPES:
        return KIND_VISION
    return KIND_MIXED


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
    source_root = target.parent if target.is_file() else target
    if not pdfs:
        print(f"未找到 PDF: {target}", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else (target.parent if target.is_file() else target) / "_md"
    out_dir.mkdir(parents=True, exist_ok=True)

    stats = {"text": 0, "vision": 0, "mixed": 0, "skip": 0, "fail": 0}
    for pdf in pdfs:
        relative = pdf.relative_to(source_root)
        meta_path = out_dir / relative.with_suffix(".meta.json")
        md_path = out_dir / relative.with_suffix(".md")
        try:
            data = pdf.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            # Hash the location to distinguish inputs without recording a private absolute path.
            source_identity = hashlib.sha256(os.path.normcase(str(pdf.resolve())).encode("utf-8")).hexdigest()
            if not args.force and meta_path.is_file():
                try:
                    cached = json.loads(meta_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    cached = {}
                if (isinstance(cached, dict) and cached.get("source_path_sha256") not in (None, source_identity)
                        and cached.get("source_sha256") != digest):
                    raise ValueError("输出已属于另一份同名PDF; 请另选 --out 或明确加 --force 覆盖")
                if (isinstance(cached, dict) and cached.get("source") == relative.as_posix()
                        and cached.get("source_sha256") == digest
                        and cached.get("source_path_sha256")
                        and (cached.get("markdown_written") is False
                             or (cached.get("markdown_written") is True and md_path.is_file()))):
                    stats["skip"] += 1
                    print(f"  跳过(源文件未变): {relative.as_posix()}")
                    continue
            res = pi.process_pdf_bytes(data)  # PdfResult: pdf_type/confidence/markdown/pages_needing_ocr/...
            ptype = str(res.pdf_type or "").lower()
            kind = classify(res.pdf_type)

            markdown = res.markdown or ""
            needs_ocr_pages = list(res.pages_needing_ocr or [])
            needs_vision = kind != "text_based" or bool(needs_ocr_pages)

            md_path.parent.mkdir(parents=True, exist_ok=True)
            if markdown:
                md_path.write_text(markdown, encoding="utf-8")
            else:
                md_path.unlink(missing_ok=True)
            meta = {
                "source": relative.as_posix(),
                "source_sha256": digest,
                "source_path_sha256": source_identity,
                "kind": kind,
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
