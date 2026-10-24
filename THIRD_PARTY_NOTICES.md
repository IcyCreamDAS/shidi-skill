# Third-party notices

This repository ships original code (MIT, see `LICENSE`) plus the following
third-party material.

## verify_refs.py

`skills/shidi/scripts/verify_refs.py` is a stdlib port of the literature-review
kernel from **OpenAI4S** (`literature-review/kernel.py`), used under the MIT
License. The port replaces the original host-provided `web_fetch` with
`urllib.request`, keeps the no-redirect HEAD semantics for DOI resolution, and
adds a deterministic style lint.

- Upstream: OpenAI4S — literature-review kernel (MIT)
- Local changes: stdlib-only I/O, CLI wrapper, style_pass, crossref_lookup,
  retraction detection
- License: MIT

## Demo assets and design references

- `assets/social-preview.png` — background generated locally with Krea 2 Turbo;
  typography composed by this repository.
- Design ideas (routing, six-dim scoring, search fallback chain, paper cards)
  borrowed from **nature-skills** (Yuan1z0825 team), MIT — see README credits.

## Open-access papers used in reading preparation

The articles under `competitions/bohrium-reading-2026-10/materials/` and their
reading derivatives are **CC BY 4.0, not MIT**. The repository MIT license does
not replace the articles' licenses. Original author credits, DOI links, source
URLs, retrieval dates, modifications and hashes are recorded in
`competitions/bohrium-reading-2026-10/materials/SOURCES.md` and `sources.json`.

- Dong et al. (2024), DOI `10.3390/polym16182572`, PMCID `PMC11435391`.
- Qi et al. (2023), DOI `10.3390/polym15173626`, PMCID `PMC10490335`.
- License: https://creativecommons.org/licenses/by/4.0/
- Unchanged JATS XML was obtained through Europe PMC. Markdown reading aids and
  an intentionally abstract-only case are identified as derivatives. Figure
  image files and supplementary files are not included.
- Pilot terminal logs may reproduce those same article excerpts; the article
  attribution and CC BY 4.0 license continue to apply to those excerpts.
