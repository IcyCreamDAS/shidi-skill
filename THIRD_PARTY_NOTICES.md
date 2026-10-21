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
