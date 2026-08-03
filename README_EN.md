# Shidi (师弟) — A Research Wish-Fulfillment Machine

[![License](https://img.shields.io/badge/license-MIT-2ea44f)](LICENSE)
[![Agent](https://img.shields.io/badge/agent-Claude%20Code%20%7C%20Codex%20%7C%20OpenClaw-111827)](README.md)
[![Zero-Dep](https://img.shields.io/badge/dependencies-zero-ff69b4)](README.md)

[中文](./README.md) | English

> **You have the idea, shidi does the dirty work.** shidi is not a template filler — it's a complete research workflow that runs inside AI IDEs: hand it a thought (literature review / experiment design / plotting / paper deep-reading / data organization), and it runs the tedious pipeline on your machine, delivering **real files** — a final report plus a cross-validation brief. Your data stays local; no platform or model lock-in.

## What It Does

| Capability | Description |
|:--|:--|
| 📚 **Literature Review** | Ask 3 parameters in one round → diverge 3×3=9 angles → top-journal targeted search + fallback chain → six-dimension scoring → tiered reading → file report |
| 🧪 **Experiment Design** | Free-form angle divergence → literature-backed principles / steps / cautions / **gap list** (no sugar-coating) |
| 📈 **Scientific Plotting** | CSV/TXT/Excel → cleaning → computation (numpy/scipy/sympy) → publication-grade rendering |
| 🔬 **Paper Deep-Reading** | source-map six-step workflow → 16-section paper card → terminology ledger |
| 🔄 **Cross-Validation Gate (the soul)** | A validation brief (md) is always delivered — hand it to *another LLM* for an independent review, iterate until you're satisfied |
| 📋 **Lab Notes** | Standardized experiment/batch IDs with YAML frontmatter |

## Quick Start

```bash
git clone https://github.com/<your-username>/shidi-skill.git
cp -r shidi-skill/skills/shidi ~/.claude/skills/
```

Then just say (in Chinese, or trigger with the skill name):

```
师弟，帮我查一下 XX 主题的文献，要 20 篇
师弟，设计一个 XX 实验方案
```

## Design Philosophy

- **You provide the idea and the drive; shidi executes.** All key decision points (angle selection, parameter confirmation, direction trade-offs) are returned to you for confirmation.
- **A tool, not a wishing well.** The workflow is free and open source; the only cost is your AI model usage. The model sets the ceiling.

## Deliverables

| Deliverable | Default location (configurable) | Notes |
|:--|:--|:--|
| 📄 Final report | `~/shidi-output/` | Markdown (default) or Word |
| ✅ Cross-validation brief | `~/shidi-verify/` | Task brief for another LLM; doubles as a self-check list |
| 🧪 Lab notes | `~/lab-notes/` | Standardized experiment/batch IDs |
| 🗂 Paper cards | `~/literature-cards/` | 16-section deep-reading cards |

## Dependencies

- **Zero external dependencies** — pure SKILL.md + Markdown.
- Optional: numpy/scipy/matplotlib/pandas/sympy for plotting (pyvista for 3D).
- Search fallback: WebSearch → open academic APIs (OpenAlex/Crossref/arXiv, no key required).

## Credits

Design inspired by [nature-skills](https://github.com/Yuan1z0825/nature-skills) (Yuan Yizhe's team): router layering, six-dimension scoring, search fallback chains, paper card mechanisms.

## License

[MIT License](LICENSE)
