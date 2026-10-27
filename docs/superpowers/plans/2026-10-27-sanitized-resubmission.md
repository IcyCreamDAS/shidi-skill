# Sanitized Resubmission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Skill and GitHub upload packages with current sanitized Pro/Flash resources while preserving original runs and making every forbidden label/company-confidential item absent.

**Architecture:** Start from current `origin/competition-materials`, retain original evidence, update only packaging metadata, public article/install text and sanitized current resources. Reuse the existing official builder and offline-material workflow, then perform full text/PDF scans, official validation and CLI dry-runs before publishing the fixed public work commit.

**Tech Stack:** Python 3, existing official submission tools, Git worktrees, GitHub API, Playground CLI 0.1.43.

**Spec:** `docs/superpowers/specs/2026-10-27-sanitized-resubmission-design.md`

## Global Constraints

- Do not rerun models or alter original reports, PDFs, traces, usage or scores.
- Record current packaged revision separately from historical Pro `b28eb4e` / Flash `6e03d72` runs.
- Forbidden material labels, “中研”, real employer/customer/NDA/company-confidential content are absent from every deliverable; tool/model names remain allowed.
- Do not formally upload either track.

## Review Focus

- Hidden labels in PDFs or SVG rather than Markdown: Task 4 extracts text from every PDF and scans all text formats.
- Current packaged Skill differing from historical runs without disclosure: Task 1 records both revisions and verifies executable files are unchanged.
- GitHub text limit changing after new notes: Task 3 recomputes raw UTF-8 bytes and enforces 245,760 bytes.
- Sensitive content returning in generated review.json/manifest/README: Task 4 scans those generated files too.
- Public work link not matching offline content: Task 3 pushes the public commit before generating submission.txt and verifies the public URL.

---

### Task 1: Verify versions and update public packaging documents

**Files:**
- Modify: `competitions/bohrium-reading-2026-10/final-submission/build_submission.py`
- Modify: `competitions/bohrium-reading-2026-10/final-submission/SUBMISSION_README.md`
- Modify: `competitions/bohrium-reading-2026-10/final-submission/SUBMISSION_REPORT.md`
- Modify: `GITHUB_SHARE.md`

**Interfaces:**
- Consumes: current sanitized resources and the original frozen runs.
- Produces: explicit current-package versus historical-run version metadata and default-main public installation text.

- [ ] **Step 1: Prove behavior-bearing files are unchanged**

Compare Pro/Flash `SKILL.md` and all scripts against the frozen versions; require expected hashes and allow only the two sanitized reference resources to differ.
Expected: no executable or workflow-logic changes.

- [ ] **Step 2: Update metadata and public documents**

Record `packaged_skill_revision`, historical run versions and documentation-only sanitization in the manifest; change installation text to default `main` and state that no new run or rescore was performed.

### Task 2: Rebuild the Skill package and trace

**Files:**
- Create: `C:/AGENTDATA/kimicode/shidi-sanitized-submission-20261027/skill/`
- Reuse: original full runs from `C:/AGENTDATA/kimicode/shidi-three-tracks-20261027/skill/full-runs/`
- Reuse: official resources from `bohrium-challenge-sequential-authenticated-02/`

**Interfaces:**
- Consumes: Task 1 builder and original full runs.
- Produces: a new official Skill ZIP, review index and 422-record source trace.

- [ ] **Step 1: Build with the official builder**

Run `final-submission/build_submission.py` with the existing full-run archive and official resources into a new output directory.
Expected: `intake_complete`, all four run/PDF sets preserved and two cases of 4 tables + 3 charts included.

- [ ] **Step 2: Regenerate the platform trace and dry-run ARM**

Convert the four existing visible exports without adding dialogue, then build the ARM with CLI 0.1.43.
Expected: 422 source records, 423 ARM records including session_start, dry-run success.

### Task 3: Rebuild the GitHub public work and offline package

**Files:**
- Modify: `C:/AGENTDATA/kimicode/shidi-three-tracks-20261027/prepare_submissions.py` into a new sanitized packaging script
- Create: `C:/AGENTDATA/kimicode/shidi-sanitized-submission-20261027/github/`

**Interfaces:**
- Consumes: the updated public commit, current sanitized workflows and original evidence.
- Produces: a fixed public work URL, materials.zip and ARM dry-run.

- [ ] **Step 1: Commit and push the public work**

Commit only Task 1 public document/resource changes on `competition/sanitized-2026-10-27`, push, and use the resulting commit in the offline package link.
Expected: public work is readable without authentication.

- [ ] **Step 2: Build the offline materials**

Use current sanitized Pro/Flash workflows and the original reports/evidence; update the submission note to distinguish current resources from historical runs.
Expected: four tables and three charts for the first case, raw UTF-8 text <=245,760 bytes, no stale feature-only installation text.

- [ ] **Step 3: Build the GitHub ARM**

Run CLI 0.1.43 dry-run with the same source trace.
Expected: materials.zip and submission.txt are both packaged successfully.

### Task 4: Perform final full-content validation

**Files:**
- Verify all files under `C:/AGENTDATA/kimicode/shidi-sanitized-submission-20261027/`

**Interfaces:**
- Consumes: both rebuilt packages and public URLs.
- Produces: upload-ready status or a named blocker.

- [ ] **Step 1: Scan every deliverable**

Scan Markdown, CSV, JSON/JSONL, SVG, TXT, Python, paths and extracted PDF text for forbidden material labels, “中研”, employer/customer/NDA/confidential terms and company-confidential data.
Expected: zero true positives; tool/model names are not treated as confidential data.

- [ ] **Step 2: Re-run structural and consistency checks**

Verify ZIP CRCs, file hashes, public URL/commit match, original report/PDF/trace hashes, Skill official intake, both ARM dry-runs and repository tests.
Expected: all pass; no formal upload or Attempt ID created.
