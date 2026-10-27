# Main Dual-Mode Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the stable Pro/Flash dual-mode Skill to main through a selective PR without importing competition artifacts.

**Architecture:** Start from current `origin/main`, copy only the router, complete mode directories, one required root reading resource and the router test from `origin/feature/shidi-pro-flash`. Preserve main-specific schema/paper-reading rules, synchronize mode schemas to main, and edit both READMEs to describe default-main installation without competition links.

**Tech Stack:** Git worktrees, Markdown, Python unittest, existing ML demo, GitHub PR flow.

**Spec:** `docs/superpowers/specs/2026-10-27-main-dual-mode-release-design.md`

## Global Constraints

- Do not add `competitions/` or `examples/pro-flash-evaluation/` files or links.
- Preserve current main's `paper-reading.md` and `data-extraction-schema.md` rules.
- Keep all anonymization changes and numeric data unchanged.
- Publish through a PR; do not push the release commit directly to main.

## Review Focus

- Competition paths hidden in documentation: Task 2 scans all changed files and validates relative links.
- Router files differing from frozen versions: Task 2 runs the router hash tests.
- Mode schemas diverging from main: Task 2 runs template identity tests.
- Release containing private traces or real formulation data: Task 2 runs the sensitive-file allowlist and label scans.
- Main changing after the PR: Task 3 checks the remote head and merges only if the PR is current.

---

### Task 1: Assemble the selective release

**Files:**
- Copy from feature: `skills/shidi/SKILL.md`, `skills/shidi/modes/`, `skills/shidi/references/focused-reading.md`, `tests/test_mode_router.py`
- Preserve from main: `skills/shidi/references/paper-reading.md`, `skills/shidi/references/data-extraction-schema.md`
- Modify: `README.md`, `README_EN.md`, `skills/shidi/modes/pro/references/data-extraction-schema.md`, `skills/shidi/modes/flash/references/data-extraction-schema.md`

**Interfaces:**
- Consumes: `origin/main=101c297` and the stable dual-mode files from `origin/feature/shidi-pro-flash=73d46d0`.
- Produces: a clean selective release tree with no competition artifacts.

- [ ] **Step 1: Verify the baseline**

Run `python -X utf8 validate.py` and `python -X utf8 -m unittest discover -s tests -q` on the new main-based worktree.
Expected: 34 checks and 40 tests pass before dual-mode files are added.

- [ ] **Step 2: Copy only the approved files**

Copy the router, complete mode directories, `focused-reading.md` and `test_mode_router.py` from the feature revision; restore main's schema and synchronize it to both modes. Do not copy competition examples or notices.

- [ ] **Step 3: Clean both READMEs**

Keep dual-mode usage, replace feature-only installation with default `git clone https://github.com/IcyCreamDAS/shidi-skill.git`, and remove real-run evaluation, technical-article and competition-material links.

### Task 2: Verify and commit the release

**Files:**
- Verify all changed files
- Modify only if a broken link or scoped regression is found

**Interfaces:**
- Consumes: the selective tree from Task 1.
- Produces: one reviewed release commit ready for PR.

- [ ] **Step 1: Run functional checks**

Run `python examples/materials_small_data/run_demo.py --quick`, `python -X utf8 validate.py`, `python -X utf8 -m unittest discover -s tests -q`, `python -X utf8 -m unittest tests.test_mode_router tests.test_materials_small_data -v`, and `git diff --check`.
Expected: all pass; router now has 18 frozen files per mode and default Pro routing.

- [ ] **Step 2: Audit scope and privacy**

List changed files; assert no `competitions/` or `examples/pro-flash-evaluation/` path exists, no trace/log files were added, and former material labels remain absent from public formulation files.
Expected: only approved Skill, docs, tests and planning files changed.

- [ ] **Step 3: Commit**

Commit as `feat: publish pro and flash modes to main`.

### Task 3: Publish through PR and verify main

**Files:**
- Verify the PR branch and resulting main

**Interfaces:**
- Consumes: the release commit from Task 2.
- Produces: a merged PR and a verified default main installation.

- [ ] **Step 1: Push and create the PR**

Push `release/pro-flash-main`, create a PR to `main` with the scope and verification evidence, and inspect the PR diff.
Expected: only the approved selective diff is visible.

- [ ] **Step 2: Merge and verify**

Merge the PR only when it is current and checks pass; fetch main, run `validate.py` and the full unit suite, and verify default installation text and absence of competition artifacts.
Expected: main contains stable Pro/Flash and all checks pass.
