# Security Policy · 安全策略

## Supported versions

The `0.x` line is maintained; fixes land on `main` and are released with the next tag.
Older tags receive fixes only if the issue is trivially patchable.

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

- Preferred: **GitHub Security Advisories** —
  *Security* tab → *Report a vulnerability* (private channel, no email needed).
- Non-sensitive bugs: use the issue form (`.github/ISSUE_TEMPLATE/bug_report.yml`).

We aim to acknowledge reports within 7 days.

## What this project touches

- **No telemetry, no analytics, no accounts.** The skill itself is pure Markdown and makes no
  network calls.
- **Optional scripts** make outbound requests only when you run them:
  | Script | Outbound endpoints | Notes |
  |---|---|---|
  | `skills/shidi/scripts/fetch_pdfs.py` | `api.openalex.org`, `api.unpaywall.org` | Open-access PDF lookup; no keys required |
  | `skills/shidi/scripts/extract_pdfs.py` | none | local `pdf-inspector` parsing |
  | `skills/shidi/scripts/render_report.py` | none | local headless Edge print |
- **No credentials** are required or stored. If you add a script that needs one, stop and open an issue first.
- **User data stays local.** The skill writes files under the working directory you point it at;
  nothing is uploaded by this repository's code.

## Data hygiene for contributors

Never commit real industrial or confidential research data. `examples/materials_small_data/`
is **synthetic by construction** and must stay that way. Redact tokens, paths, and customer names
from screenshots, logs and issue reports.

## Dependencies

The example uses `numpy` + `scikit-learn` pinned by `examples/materials_small_data/requirements.txt`;
CI installs them from PyPI. The shipped bundle has no runtime dependencies beyond the DSH host.
