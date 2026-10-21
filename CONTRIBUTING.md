# Contributing · 贡献指南

Thanks for helping. This repository ships one SKILL.md-based research workflow
(`skills/shidi/`) plus a thin DSH bundle wrapper (`index.mjs` + `cordis.patch.yml`).

## 欢迎的贡献 / What we welcome

- **Skill content** — new reference material, search-fallback fixes, scoring fixes under `skills/shidi/`
- **Scripts** — fixes to `fetch_pdfs.py` / `extract_pdfs.py` / `render_report.py`
- **Docs** — README, `examples/`, translations, issue triage
- **Never submit** — real company/university formulation data, lab measurements that are not
  yours to publish, unredacted screenshots, tokens or keys. `examples/` uses synthetic data only.

## 提交前检查 / Before opening a PR

1. `python validate.py` must pass (CI runs the same script).
2. If you touched the example: `cd examples/materials_small_data && python run_demo.py --quick`.
3. Relative links/images in the READMEs must resolve (`validate.py` checks them).
4. If you touch `package.json` or a version badge, keep them equal — CI fails otherwise.
5. **YAML trap:** any scalar containing `": "` must be quoted. This repository has already been
   bitten by it: a submission to an awesome-list failed to parse for exactly this reason.
   Run `python validate.py` (or `make schema_check` in the consuming list) before pushing.

> [!NOTE]
> 中文提醒：任何含 `: ` 的 YAML 字符串必须加引号；这是本仓库真实踩过的坑。

## PR 流程 / Pull requests

- Fork → branch → open a PR (the PR template appears automatically).
- One PR, one concern. Draft PRs are fine for early feedback.
- Keep commits scoped; messages use `feat:` / `fix:` / `docs:` / `chore:` / `test:` plus one line
  (Chinese or English both welcome).
- Be civil: critique the change, not the person. For scientific claims, attach evidence or a citation.

## 版本与发布 / Versioning and releases

- The maintainer bumps `package.json` + README badges + git tag + npm release together.
  Third-party PRs do **not** need a version bump.
- `package.json`, both README badges and the git tag must agree; `validate.py` enforces the first two.

## License

By contributing you agree that your contribution is licensed under the MIT License (`LICENSE`).
