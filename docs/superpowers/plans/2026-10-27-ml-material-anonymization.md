# ML Material Anonymization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all material labels in public ML/product formulation examples with filler, additive A, additive B and matrix while preserving every numeric value and model result.

**Architecture:** Apply one role-mapping contract across the ML generator, stored CSV, modeling script, README files and current Skill templates. A focused regression test guards the public file set, canonical numeric hash and generator reproducibility; frozen competition evidence remains untouched.

**Tech Stack:** Python 3, stdlib csv/unittest, existing scikit-learn demo, Git worktrees.

**Spec:** `docs/superpowers/specs/2026-10-27-ml-material-anonymization-design.md`

## Global Constraints

- Roles are exactly `filler`, `additive_a`, `additive_b`, `matrix`; Chinese labels are 填料、添加剂 A、添加剂 B、基体.
- Keep all 120 rows, all numeric cells, the random seed and model logic unchanged.
- Do not modify `competitions/` or frozen resources under `examples/pro-flash-evaluation/`.
- Synchronize the same scoped change to `main`, `feature/shidi-pro-flash` and `competition-materials` without merging their other differences.

## Review Focus

- Material names hidden in prose rather than column names: Task 1 scans every public usage file, including both root READMEs and all current Skill template copies.
- Numeric changes accidentally introduced during renaming: Task 1 pins canonical numeric SHA-256 `311e7bdb37301f8eb50256ee0bb35bac5499a0089df1d60c7317aa167670c7de`.
- Generator and CSV drifting apart: Task 1 regenerates all rows and compares values.
- Pro/Flash template copies becoming inconsistent: Task 2 checks their schema and template bytes match the current shared versions.
- Demo behavior changing despite text-only edits: Task 3 runs `run_demo.py --quick`, `validate.py` and the complete unit suite.

---

### Task 1: Add anonymization regression checks

**Files:**
- Create: `tests/test_materials_small_data.py`
- Test: `tests/test_materials_small_data.py`

**Interfaces:**
- Consumes: the six tracked files in `examples/materials_small_data/`, both root READMEs, and the current shared/Pro/Flash schema and CSV template files.
- Produces: `PUBLIC_FORMULATION_FILES`, `VALUE_KEYS`, `test_public_formulation_files_use_roles_only`, `test_synthetic_values_and_generator_are_unchanged`.

- [ ] **Step 1: Write the failing tests**

Create tests asserting:
- Every public formulation file contains none of the former specific material or role labels, including polymer/additive names and old column identifiers.
- CSV columns are exactly `project,sample,matrix_grade,filler_wt_pct,additive_a_wt_pct,additive_b_wt_pct,matrix_wt_pct,melt_temp_C,tensile_MPa,flexural_modulus_GPa,MFR_g_per_10min,data_source`.
- All 120 rows are `synthetic`; canonical numeric values hash to the value above; generated rows match stored rows; closure tolerance remains valid.
- Shared, Pro and Flash schema/template copies are byte-identical.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -X utf8 -m unittest tests.test_materials_small_data -v`
Expected: FAIL on the former labels in the public files.

### Task 2: Apply the role-mapping contract

**Files:**
- Modify: `examples/materials_small_data/README.md`
- Modify: `examples/materials_small_data/make_synthetic_data.py`
- Modify: `examples/materials_small_data/run_demo.py`
- Modify: `examples/materials_small_data/priors_template.csv`
- Modify: `examples/materials_small_data/data/synthetic_formulations.csv`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `skills/shidi/references/data-extraction-schema.md`
- Modify: `skills/shidi/references/templates/formulation_properties.csv`
- Modify: `skills/shidi/modes/pro/references/data-extraction-schema.md`
- Modify: `skills/shidi/modes/pro/references/templates/formulation_properties.csv`
- Modify: `skills/shidi/modes/flash/references/data-extraction-schema.md`
- Modify: `skills/shidi/modes/flash/references/templates/formulation_properties.csv`
- Test: `tests/test_materials_small_data.py`

**Interfaces:**
- Consumes: former `gf/resin/coupling/lubricant` identifiers and material examples.
- Produces: `matrix_grade`, `filler_wt_pct`, `additive_a_wt_pct`, `additive_b_wt_pct`, `matrix_wt_pct`; equivalent variable names and role-only prose.

- [ ] **Step 1: Apply exact column mapping**

Use `gf_wt_pct→filler_wt_pct`, `coupling_agent_wt_pct→additive_a_wt_pct`, `lubricant_wt_pct→additive_b_wt_pct`, `resin_wt_pct→matrix_wt_pct`, `resin_grade→matrix_grade`; keep column order and every value unchanged.

- [ ] **Step 2: Rename code variables and prose without changing formulas**

Use `filler`, `additive_a`, `additive_b`, `matrix` and `matrix_effect`; replace all specific material examples in public usage files with these roles or `example-system`. Do not alter random generation, equations, models, units, outputs or dependencies.

- [ ] **Step 3: Run focused tests**

Run: `python -X utf8 -m unittest tests.test_materials_small_data -v`
Expected: all checks PASS.

- [ ] **Step 4: Commit the scoped change and planning documents**

```bash
git add README.md README_EN.md examples/materials_small_data skills/shidi/references skills/shidi/modes tests/test_materials_small_data.py docs/superpowers
git commit -m "refactor: anonymize formulation material roles"
```

### Task 3: Verify the deliverable and publish feature/main

**Files:**
- Verify: all files from Tasks 1–2
- Create outside the repository: main worktree `C:/AGENTDATA/kimicode/shidi-main-release`

**Interfaces:**
- Consumes: the scoped commit from Task 2 and `origin/main`.
- Produces: identical scoped commits on public `feature/shidi-pro-flash` and `main`.

- [ ] **Step 1: Run functional and repository checks**

Run `python examples/materials_small_data/run_demo.py --quick`, `python -X utf8 validate.py`, `python -X utf8 -m unittest discover -s tests -q`, and `git diff --check`.
Expected: demo exits 0, 49 validation checks pass, unit suite is OK, no whitespace errors.

- [ ] **Step 2: Scan the final public file set**

Run the focused test and a case-insensitive label scan limited to the files from Task 2.
Expected: no former material labels; frozen competition evidence was not modified.

- [ ] **Step 3: Push feature and create the main worktree**

Push `feature/shidi-pro-flash`; create the main worktree from `origin/main` using the required worktree skill, cherry-pick the scoped commit, repeat Step 1 on main, and push `main`.

### Task 4: Synchronize competition-materials

**Files:**
- Modify only through cherry-pick in `C:/AGENTDATA/Harness共通/transfer/competition/2026-10-27-shidi-local/competition-materials-review-fix`

**Interfaces:**
- Consumes: the scoped commit from Task 2.
- Produces: the same role-only public files on `competition-materials`.

- [ ] **Step 1: Cherry-pick and verify**

Cherry-pick the scoped commit, run `validate.py`, the complete unit suite and the focused anonymization test.
Expected: all pass; no unrelated branch files changed.

- [ ] **Step 2: Push and verify remote heads**

Push `competition-materials`; use `git ls-remote` to confirm all three public heads, then confirm each worktree is clean.
