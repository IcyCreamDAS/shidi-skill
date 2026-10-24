#!/usr/bin/env python3
"""Produce a deterministic reading aid; the unchanged JATS XML is authoritative."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def text(node):
    return " ".join("".join(node.itertext()).split()) if node is not None else ""


def render(source):
    root = ET.parse(source).getroot()
    seen = set()
    lines = ["# " + text(root.find(".//article-title")),
             "", "Reading aid derived from JATS XML. Original XML is authoritative.",
             "Figures are captions only; image pixels are not included.",
             "MathML equations and merged table cells must be checked in the XML.", ""]
    for item in root.findall(".//article-id"):
        lines.append(f"{item.get('pub-id-type', 'id')}: {text(item)}")
    for item in root.findall(".//license"):
        lines.extend(["", text(item)])

    def walk(node, depth=2):
        for child in node:
            tag = child.tag.rsplit("}", 1)[-1]
            anchor = child.get("id", "")
            if tag in {"sec", "abstract"}:
                lines.extend(["", "#" * min(depth, 6) + " " +
                              (text(child.find("title")) or tag) + f" [{anchor}]", ""])
                walk(child, depth + 1)
            elif tag == "title":
                continue
            elif tag == "table-wrap":
                if child in seen:
                    continue
                seen.add(child)
                lines.extend(["", f"### {text(child.find('label'))} [{anchor}]",
                              text(child.find("caption")), ""])
                for row in child.findall(".//tr"):
                    cells = []
                    for cell in row:
                        spans = " ".join(f"{a}={cell.get(a)}" for a in ("rowspan", "colspan")
                                         if cell.get(a) not in (None, "1"))
                        cells.append(text(cell) + (f" [{spans}]" if spans else ""))
                    lines.append(" | ".join(cells))
                lines.append("")
            elif tag == "fig":
                if child in seen:
                    continue
                seen.add(child)
                lines.extend(["", f"{text(child.find('label'))} [{anchor}] (caption only): " +
                              text(child.find("caption")), ""])
            elif tag in {"p", "list-item", "statement"}:
                lines.extend([text(child), ""])
                # Some JATS exports embed figures/tables inside paragraphs.
                for nested in child:
                    if nested.tag in {"table-wrap", "fig"}:
                        wrapper = ET.Element("wrapper")
                        wrapper.append(nested)
                        walk(wrapper, depth)
            elif tag in {"disp-formula", "inline-formula"}:
                lines.extend([f"Equation [{anchor}]: see original XML MathML.", ""])
            elif tag in {"body", "boxed-text", "list"}:
                walk(child, depth)

    front = root.find("front/article-meta")
    if front is not None:
        for abstract in front.findall("abstract"):
            wrapper = ET.Element("wrapper")
            wrapper.append(abstract)
            walk(wrapper)
    body = root.find("body")
    if body is not None:
        walk(body)
    # PMC may store floats outside <body>; keep those tables and captions too.
    floats = [n for n in root.iter() if n.tag in {"table-wrap", "fig"} and n not in seen]
    if floats:
        lines.extend(["", "## Floating figures and tables", ""])
        wrapper = ET.Element("wrapper")
        wrapper.extend(floats)
        walk(wrapper)
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(render(args.source), encoding="utf-8")
