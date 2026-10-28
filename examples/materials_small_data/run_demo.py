#!/usr/bin/env python3
"""Small-data materials ML demo on a fully synthetic role-based dataset.

What it demonstrates
  1. grouped validation (leave-one-project-out) instead of a random split;
  2. a Gaussian-process surrogate with per-feature ARD length scales, an
     uncertainty calibration table (zero-shot vs 1-2 anchor runs) and an
     honest reading of +/-1 sigma / +/-2 sigma coverage;
  3. constrained candidate search with the joint acquisition
     ECI(x) = EI(x) * P(MFR(x) >= constraint) - no hard feasibility cutoff;
  4. a Pareto front for tensile strength vs MFR (independent GPs, so
     correlated outputs are a documented simplification);
  5. a simulated closed loop (propose -> synthetic oracle -> refit);
  6. explicit claim labels measured / predicted / exploratory.

The synthetic recipes satisfy the mass-fraction closure constraint
(filler + additive_a + additive_b + matrix = 100 wt%), and candidate
sampling keeps matrix >= 40 wt%.

Usage
    python run_demo.py                       # full demo (seconds)
    python run_demo.py --quick               # smaller pool, 1 AL round (CI)
    python run_demo.py --priors priors_template.csv   # literature-derived bounds
    python run_demo.py --regenerate          # regenerate the synthetic table

Outputs (git-ignored, regenerated on every run)
    outputs/report.md
    outputs/logo_metrics.csv
    outputs/calibration.csv
    outputs/candidates.csv
    outputs/pareto.csv
    outputs/active_learning.csv

All data is synthetic (see make_synthetic_data.py). This directory must never
contain real industrial formulations or measurements.
"""
from __future__ import annotations

import argparse
import csv
import math
import warnings
from pathlib import Path

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from make_synthetic_data import (
    DATA_FILE,
    assert_closed,
    build_rows,
    true_mfr,
    true_modulus,
    true_tensile,
    write_csv as write_synthetic,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs"
TARGETS = ("tensile_MPa", "flexural_modulus_GPa", "MFR_g_per_10min")
FEATURE_NAMES = (
    "filler_wt_pct",
    "additive_a_wt_pct",
    "additive_b_wt_pct",
    "melt_temp_C (centered / 20)",
    "matrix_grade == A",
    "matrix_grade == B",
)
MFR_CONSTRAINT = 28.0
FEASIBILITY = 0.80
ANCHOR_COUNTS = (0, 1, 2)
SEED = 20261021

DEFAULT_BOUNDS = {
    "filler_wt_pct": (10.0, 45.0),
    "additive_a_wt_pct": (0.2, 1.2),
    "additive_b_wt_pct": (0.1, 0.8),
    "melt_temp_C": (345.0, 378.0),
}
MATRIX_FLOOR = 40.0  # candidate recipes keep matrix >= 40 wt%

CLAIM_LABELS = [
    ("measured", "a real observation from the dataset"),
    ("predicted", "model output with uncertainty; not verified by experiment"),
    ("exploratory", "a screening recommendation; never report it as a result"),
]

CANDIDATE_FIELDS = [
    "rank",
    "claim_label",
    "feasible",
    "matrix_grade",
    "filler_wt_pct",
    "additive_a_wt_pct",
    "additive_b_wt_pct",
    "matrix_wt_pct",
    "melt_temp_C",
    "tensile_pred_MPa",
    "tensile_sd_MPa",
    "tensile_screening_low",
    "tensile_screening_high",
    "mfr_pred_g_per_10min",
    "mfr_sd_g_per_10min",
    "p_mfr_feasible",
    "ei",
    "eci",
]
PARETO_FIELDS = [
    "rank",
    "claim_label",
    "feasible",
    "matrix_grade",
    "filler_wt_pct",
    "additive_a_wt_pct",
    "additive_b_wt_pct",
    "matrix_wt_pct",
    "melt_temp_C",
    "tensile_pred_MPa",
    "tensile_sd_MPa",
    "mfr_pred_g_per_10min",
    "mfr_sd_g_per_10min",
    "p_mfr_feasible",
]


def load_rows(path=DATA_FILE):
    with Path(path).open(encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def features(rows):
    matrix = []
    for row in rows:
        grade = row["matrix_grade"]
        matrix.append(
            [
                float(row["filler_wt_pct"]),
                float(row["additive_a_wt_pct"]),
                float(row["additive_b_wt_pct"]),
                (float(row["melt_temp_C"]) - 360.0) / 20.0,
                1.0 if grade == "A" else 0.0,
                1.0 if grade == "B" else 0.0,
            ]
        )
    return np.asarray(matrix, dtype=float)


def targets(rows, name):
    return np.asarray([float(row[name]) for row in rows], dtype=float)


def make_gp(n_features):
    kernel = ConstantKernel(1.0, (1e-2, 1e3)) * RBF(np.ones(n_features), (1e-2, 1e2))
    kernel = kernel + WhiteKernel(1e-1, (1e-3, 1e1))
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("gp", GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=0)),
        ]
    )


def fit_target(rows, target):
    x = features(rows)
    model = make_gp(x.shape[1])
    model.fit(x, targets(rows, target))
    return model


def find_rbf(kernel):
    if isinstance(kernel, RBF):
        return kernel
    for attr in ("k1", "k2"):
        sub = getattr(kernel, attr, None)
        if sub is not None:
            found = find_rbf(sub)
            if found is not None:
                return found
    return None


def ard_length_scales(model):
    """Optimized per-feature length scales (smaller = feature matters more)."""
    rbf = find_rbf(model.named_steps["gp"].kernel_)
    if rbf is None:
        return []
    return [float(value) for value in np.atleast_1d(np.asarray(rbf.length_scale, dtype=float))]


def logo_validation(rows, target):
    """Leave-one-project-out: every fold holds out a whole project."""
    groups = sorted({row["project"] for row in rows})
    y_true, mu_gp, sd_gp, mu_ridge = [], [], [], []
    for group in groups:
        train = [row for row in rows if row["project"] != group]
        test = [row for row in rows if row["project"] == group]
        model = fit_target(train, target)
        mu, sd = model.predict(features(test), return_std=True)
        ridge = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
        ridge.fit(features(train), targets(train, target))
        y_true.extend(targets(test, target).tolist())
        mu_gp.extend(mu.tolist())
        sd_gp.extend(sd.tolist())
        mu_ridge.extend(ridge.predict(features(test)).tolist())
    y = np.asarray(y_true)
    mean = np.asarray(mu_gp)
    std = np.maximum(np.asarray(sd_gp), 1e-9)
    ridge_mean = np.asarray(mu_ridge)
    z = (y - mean) / std
    return {
        "target": target,
        "n_holdout": int(y.size),
        "n_groups": len(groups),
        "r2_gp": float(r2_score(y, mean)),
        "rmse_gp": float(math.sqrt(mean_squared_error(y, mean))),
        "r2_ridge": float(r2_score(y, ridge_mean)),
        "rmse_ridge": float(math.sqrt(mean_squared_error(y, ridge_mean))),
        "coverage_1s": float(np.mean(np.abs(z) <= 1.0)),
        "coverage_2s": float(np.mean(np.abs(z) <= 2.0)),
    }


def anchored_logo(rows, target, anchors=ANCHOR_COUNTS):
    """Zero-shot vs 1-/2-anchor batch calibration on the same held-out samples.

    For every project, the last (len - max_anchor) samples are the evaluation
    set. With a anchors, the first a samples of the held-out project are added
    to the training set (the standard "run a couple of benchmark formulations
    at the new site and refit" move). All settings score the same samples.
    """
    groups = sorted({row["project"] for row in rows})
    max_anchor = max(anchors)
    stats = {a: {"y": [], "mu": [], "sd": []} for a in anchors}
    for group in groups:
        group_rows = [row for row in rows if row["project"] == group]
        if len(group_rows) <= max_anchor + 2:
            continue
        holdout = group_rows[max_anchor:]
        others = [row for row in rows if row["project"] != group]
        for a in anchors:
            train = others + group_rows[:a]
            model = fit_target(train, target)
            mu, sd = model.predict(features(holdout), return_std=True)
            stats[a]["y"].extend(targets(holdout, target).tolist())
            stats[a]["mu"].extend(mu.tolist())
            stats[a]["sd"].extend(sd.tolist())
    result = {}
    for a in anchors:
        y = np.asarray(stats[a]["y"])
        mean = np.asarray(stats[a]["mu"])
        std = np.maximum(np.asarray(stats[a]["sd"]), 1e-9)
        z = (y - mean) / std
        result[a] = {
            "target": target,
            "anchors": a,
            "n": int(y.size),
            "rmse": float(math.sqrt(mean_squared_error(y, mean))),
            "coverage_1s": float(np.mean(np.abs(z) <= 1.0)),
            "coverage_2s": float(np.mean(np.abs(z) <= 2.0)),
        }
    return result


def normal_cdf(value):
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def normal_pdf(value):
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def expected_improvement(mean, sd, best):
    sd = max(sd, 1e-9)
    z = (mean - best) / sd
    return (mean - best) * normal_cdf(z) + sd * normal_pdf(z)


def load_priors(path, bounds=None):
    """Read feature,min,max rows and return updated bounds + the applied table."""
    bounds = dict(bounds or DEFAULT_BOUNDS)
    applied = []
    with Path(path).open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            feature = (row.get("feature") or "").strip()
            if feature not in bounds:
                raise ValueError(f"priors: unknown feature {feature!r}; known: {', '.join(bounds)}")
            low = float(row["min"])
            high = float(row["max"])
            if not low < high:
                raise ValueError(f"priors: {feature} min >= max")
            bounds[feature] = (low, high)
            applied.append({"feature": feature, "min": low, "max": high,
                            "note": (row.get("note") or "").strip()})
    if not applied:
        raise ValueError("priors: no rows found")
    return bounds, applied


def candidate_pool(count, rng, bounds):
    grades = ("A", "B", "C")
    pool = []
    attempts = 0
    limit = count * 20
    while len(pool) < count and attempts < limit:
        attempts += 1
        filler = rng.uniform(*bounds["filler_wt_pct"])
        additive_a = rng.uniform(*bounds["additive_a_wt_pct"])
        additive_b = rng.uniform(*bounds["additive_b_wt_pct"])
        if filler + additive_a + additive_b > 100.0 - MATRIX_FLOOR:
            continue
        matrix = 100.0 - filler - additive_a - additive_b
        pool.append(
            {
                "matrix_grade": grades[int(rng.integers(0, len(grades)))],
                "filler_wt_pct": round(filler, 1),
                "additive_a_wt_pct": round(additive_a, 2),
                "additive_b_wt_pct": round(additive_b, 2),
                "matrix_wt_pct": round(matrix, 2),
                "melt_temp_C": round(rng.uniform(*bounds["melt_temp_C"]), 1),
            }
        )
    return pool


def _candidate_record(base, mu_t, sd_t, mu_m, sd_m, p_ok, ei, eci):
    record = dict(base)
    record.update(
        {
            "claim_label": "exploratory",
            "feasible": bool(p_ok >= FEASIBILITY),
            "tensile_pred_MPa": round(float(mu_t), 2),
            "tensile_sd_MPa": round(float(sd_t), 2),
            "tensile_screening_low": round(float(mu_t - 2.0 * sd_t), 2),
            "tensile_screening_high": round(float(mu_t + 2.0 * sd_t), 2),
            "mfr_pred_g_per_10min": round(float(mu_m), 2),
            "mfr_sd_g_per_10min": round(float(sd_m), 2),
            "p_mfr_feasible": round(float(p_ok), 3),
        }
    )
    if ei is not None:
        record["ei"] = round(float(ei), 3)
    if eci is not None:
        record["eci"] = round(float(eci), 3)
    return record


def recommend(rows, pool, top_k=8):
    """Rank candidates by joint ECI = EI(tensile) * P(MFR >= constraint)."""
    tensile_model = fit_target(rows, "tensile_MPa")
    mfr_model = fit_target(rows, "MFR_g_per_10min")
    x_pool = features(pool)
    mu_t, sd_t = tensile_model.predict(x_pool, return_std=True)
    mu_m, sd_m = mfr_model.predict(x_pool, return_std=True)
    # incumbent = best observed tensile among rows that already satisfy the
    # processability constraint (fall back to the global best if none do)
    feasible_rows = [row for row in rows if float(row["MFR_g_per_10min"]) >= MFR_CONSTRAINT]
    incumbent_rows = feasible_rows or rows
    best = float(np.max(targets(incumbent_rows, "tensile_MPa")))
    p_ok = np.asarray(
        [normal_cdf((m - MFR_CONSTRAINT) / max(float(s), 1e-9)) for m, s in zip(mu_m, sd_m)]
    )
    ei = np.asarray([expected_improvement(float(m), float(s), best) for m, s in zip(mu_t, sd_t)])
    eci = ei * p_ok

    picked = []
    for index in np.argsort(-eci):
        record = _candidate_record(
            dict(pool[int(index)]),
            mu_t[index], sd_t[index], mu_m[index], sd_m[index], p_ok[index], ei[index], eci[index],
        )
        record["rank"] = len(picked) + 1
        picked.append(record)
        if len(picked) >= top_k:
            break

    # same acquisition restricted to candidates that actually satisfy the
    # processability constraint; reported next to the ECI list for comparison
    feasible_order = [index for index in np.argsort(-eci) if p_ok[index] >= FEASIBILITY]
    feasible_picked = []
    for index in feasible_order[:3]:
        record = _candidate_record(
            dict(pool[int(index)]),
            mu_t[index], sd_t[index], mu_m[index], sd_m[index], p_ok[index], ei[index], eci[index],
        )
        record["rank"] = len(feasible_picked) + 1
        feasible_picked.append(record)
    return {
        "picked": picked,
        "picked_feasible": feasible_picked,
        "n_candidates": len(pool),
        "n_feasible": int(np.sum(p_ok >= FEASIBILITY)),
        "best_observed": best,
    }


def pareto_candidates(rows, pool, top_k=6):
    """Non-dominated tensile-vs-MFR posterior means (both maximised)."""
    tensile_model = fit_target(rows, "tensile_MPa")
    mfr_model = fit_target(rows, "MFR_g_per_10min")
    x_pool = features(pool)
    mu_t, sd_t = tensile_model.predict(x_pool, return_std=True)
    mu_m, sd_m = mfr_model.predict(x_pool, return_std=True)
    p_ok = np.asarray(
        [normal_cdf((m - MFR_CONSTRAINT) / max(float(s), 1e-9)) for m, s in zip(mu_m, sd_m)]
    )
    points = []
    for index in range(len(pool)):
        record = _candidate_record(
            dict(pool[index]), mu_t[index], sd_t[index], mu_m[index], sd_m[index], p_ok[index], None, None
        )
        record["_t"] = float(mu_t[index])
        record["_m"] = float(mu_m[index])
        points.append(record)
    ordered = sorted(points, key=lambda item: (-item["_t"], -item["_m"]))
    front = []
    best_mfr = -math.inf
    for item in ordered:
        if item["_m"] > best_mfr:
            front.append(item)
            best_mfr = item["_m"]
    front.sort(key=lambda item: -item["_t"])
    for index, item in enumerate(front[:top_k], start=1):
        item["rank"] = index
        item.pop("_t", None)
        item.pop("_m", None)
    return front[:top_k]


def simulate_experiment(candidate, rng):
    """Synthetic oracle: the known ground-truth generator plus measurement noise."""
    filler = float(candidate["filler_wt_pct"])
    additive_a = float(candidate["additive_a_wt_pct"])
    additive_b = float(candidate["additive_b_wt_pct"])
    melt = float(candidate["melt_temp_C"])
    grade = candidate["matrix_grade"]
    return {
        "tensile_MPa": round(max(5.0, true_tensile(filler, additive_a, melt, grade) + float(rng.normal(0.0, 2.2))), 2),
        "flexural_modulus_GPa": round(max(0.5, true_modulus(filler, additive_a, grade) + float(rng.normal(0.0, 0.14))), 3),
        "MFR_g_per_10min": round(max(0.5, true_mfr(filler, additive_b, melt, grade) + float(rng.normal(0.0, 1.4))), 2),
    }


def active_learning(rows, rounds, pool_size, rng, bounds):
    train = list(rows)
    history = []
    for round_no in range(1, rounds + 1):
        result = recommend(train, candidate_pool(pool_size, rng, bounds), top_k=1)
        if not result["picked"]:
            break
        candidate = (result["picked_feasible"] or result["picked"])[0]
        observed = simulate_experiment(candidate, rng)
        record = {
            key: candidate[key]
            for key in ("matrix_grade", "filler_wt_pct", "additive_a_wt_pct",
                        "additive_b_wt_pct", "matrix_wt_pct", "melt_temp_C")
        }
        record.update(observed)
        record.update({"project": "P03", "sample": f"AL{round_no:02d}", "data_source": "simulated"})
        train.append(record)
        history.append(
            {
                "round": round_no,
                "matrix_grade": candidate["matrix_grade"],
                "filler_wt_pct": candidate["filler_wt_pct"],
                "pred_tensile_MPa": candidate["tensile_pred_MPa"],
                "pred_sd_MPa": candidate["tensile_sd_MPa"],
                "observed_tensile_MPa": observed["tensile_MPa"],
                "pred_mfr": candidate["mfr_pred_g_per_10min"],
                "observed_mfr": observed["MFR_g_per_10min"],
            }
        )
    return history


def write_rows(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return path
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return path


def output_correlations(rows):
    names = list(TARGETS)
    matrix = np.corrcoef(np.vstack([targets(rows, name) for name in names]))
    return names, matrix


def build_report(rows, metrics, calibration, recommendation, pareto, history,
                 bounds, priors, ard, corr, quick):
    lines = []
    add = lines.append
    add("# Materials small-data ML demo (synthetic)")
    add("")
    add("This report is generated by run_demo.py. The dataset is synthetic by construction")
    add("(see make_synthetic_data.py); no industrial or experimental data is involved.")
    add("")
    add("## Dataset")
    add("")
    add(f"- rows: {len(rows)}; projects: {len({row['project'] for row in rows})}; "
        f"targets: {', '.join(TARGETS)}")
    add("- mass fractions close to 100 wt% per row (filler + additive_a +")
    add("  additive_b + matrix); the generator asserts this before any modelling")
    add("- inputs: filler load, additive_a, additive_b, melt temperature, matrix grade")
    add("- candidates keep matrix >= 40 wt% (no physically impossible recipes)")
    add("")
    add("## Search space")
    add("")
    add("| feature | min | max |")
    add("|---|---|---|")
    for name, (low, high) in bounds.items():
        add(f"| {name} | {low:g} | {high:g} |")
    add("")
    if priors:
        add("Bounds overridden from the literature priors file:")
        add("")
        add("| feature | min | max | note |")
        add("|---|---|---|---|")
        for item in priors:
            add(f"| {item['feature']} | {item['min']:g} | {item['max']:g} | {item['note']} |")
        add("")
        add("Priors only constrain the search space. They are not a prior mean and do not")
        add("inject literature numbers into the model; collect more data to test them.")
        add("")
    add("## Grouped validation (leave-one-project-out)")
    add("")
    add("| target | n | GP R2 | GP RMSE | Ridge R2 | Ridge RMSE | coverage +/-1s | coverage +/-2s |")
    add("|---|---|---|---|---|---|---|---|")
    for item in metrics:
        add(
            f"| {item['target']} | {item['n_holdout']} | {item['r2_gp']:+.2f} | {item['rmse_gp']:.3f} | "
            f"{item['r2_ridge']:+.2f} | {item['rmse_ridge']:.3f} | "
            f"{item['coverage_1s']:.0%} | {item['coverage_2s']:.0%} |"
        )
    add("")
    add("Calibrated Gaussian targets are 68% (+/-1 sigma) and 95% (+/-2 sigma).")
    add("")
    add("## Calibration: zero-shot vs 1-2 anchor runs")
    add("")
    add("A new project cannot be predicted from other projects alone when it carries a")
    add("batch/line offset. With a anchors, the first a formulations of the held-out")
    add("project are added to the training set (the standard \"run two benchmarks at the")
    add("new site and refit\" move). All settings score the same held-out samples.")
    add("")
    add("| target | anchors | n | RMSE | coverage +/-1s | coverage +/-2s |")
    add("|---|---|---|---|---|---|")
    for target in TARGETS:
        for a in ANCHOR_COUNTS:
            item = calibration[target][a]
            add(
                f"| {target} | {a} | {item['n']} | {item['rmse']:.3f} | "
                f"{item['coverage_1s']:.0%} | {item['coverage_2s']:.0%} |"
            )
    add("")
    zero_one = np.mean([calibration[t][0]["coverage_1s"] for t in TARGETS])
    two_one = np.mean([calibration[t][2]["coverage_1s"] for t in TARGETS])
    add(f"Mean +/-1 sigma coverage: zero-shot {zero_one:.0%}, two anchors {two_one:.0%}.")
    if two_one - zero_one < 0.05:
        add("Two anchor runs do not materially move the coverage: with a smooth ARD kernel and")
        add("edge-of-range anchors, the new project's offset is not identifiable from one or two")
        add("points. Do not assume calibration worked - measure it. A mixed-effects GP (random")
        add("project intercept) is the principled fix and is out of scope for this demo.")
    else:
        add(f"Anchor runs move the mean +/-1 sigma coverage from {zero_one:.0%} to {two_one:.0%}.")
    if two_one < 0.65:
        add("Coverage stays below the 68% target, so the exploration band remains an exploration")
        add("range, NOT a statistical confidence interval.")
    add("")
    add("## Feature relevance (ARD length scales)")
    add("")
    add("Length scales are optimized on standardized features; a smaller value means the")
    add("function varies faster along that feature (more influential).")
    add("")
    add("| feature | length scale |")
    add("|---|---|")
    for name, value in zip(FEATURE_NAMES, ard):
        add(f"| {name} | {value:.3f} |")
    add("")
    add("## Output correlations")
    add("")
    add("| | " + " | ".join(corr[0]) + " |")
    add("|---|" + "|".join(["---"] * len(corr[0])) + "|")
    for name, row in zip(corr[0], corr[1]):
        add(f"| {name} | " + " | ".join(f"{value:+.2f}" for value in row) + " |")
    add("")
    add("Strong output correlation means independent single-output GPs throw information")
    add("away; a multi-task GP would be the next step (documented as a limitation).")
    add("")
    add("## Constrained candidate search")
    add("")
    add("Acquisition is the joint expected constrained improvement")
    add("ECI(x) = EI(x) * P(MFR(x) >= constraint), so high-uncertainty candidates near")
    add("the feasibility boundary are not silently cut off by a hard filter.")
    add("")
    add(f"- constraint: P(MFR >= {MFR_CONSTRAINT:g} g/10min) >= {FEASIBILITY:.0%} "
        f"(reported as a flag, not used to filter)")
    add(f"- feasible candidates in the pool: {recommendation['n_feasible']} of {recommendation['n_candidates']}")
    add(f"- incumbent (best observed tensile among feasible rows): {recommendation['best_observed']:.1f} MPa")
    add("")
    add("The first table ranks by ECI alone. Candidates that are unlikely to meet the MFR")
    add("constraint stay visible (with their P(MFR ok) flag) instead of being silently cut;")
    add("the second table serves the strict processability requirement.")
    add("")
    add("| rank | matrix | filler wt% | additive_a wt% | additive_b wt% | matrix wt% | tensile pred MPa | sd | screening range | MFR pred | P(MFR ok) | ECI |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for item in recommendation["picked"]:
        add(
            f"| {item['rank']} | {item['matrix_grade']} | {item['filler_wt_pct']} | {item['additive_a_wt_pct']} | "
            f"{item['additive_b_wt_pct']} | {item['matrix_wt_pct']} | {item['tensile_pred_MPa']} | "
            f"{item['tensile_sd_MPa']} | [{item['tensile_screening_low']}, {item['tensile_screening_high']}] | "
            f"{item['mfr_pred_g_per_10min']} | {item['p_mfr_feasible']:.0%} | {item['eci']} |"
        )
    add("")
    add("ECI ranking restricted to candidates with P(MFR >= constraint) >= threshold:")
    add("")
    add("| rank | matrix | filler wt% | additive_a wt% | additive_b wt% | matrix wt% | tensile pred MPa | sd | MFR pred | P(MFR ok) | ECI |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for item in recommendation["picked_feasible"]:
        add(
            f"| {item['rank']} | {item['matrix_grade']} | {item['filler_wt_pct']} | {item['additive_a_wt_pct']} | "
            f"{item['additive_b_wt_pct']} | {item['matrix_wt_pct']} | {item['tensile_pred_MPa']} | "
            f"{item['tensile_sd_MPa']} | {item['mfr_pred_g_per_10min']} | {item['p_mfr_feasible']:.0%} | {item['eci']} |"
        )
    add("")
    add("The screening range is mean +/- 2 sd of the surrogate: an exploration band,")
    add("NOT a statistical confidence interval (see the calibration table).")
    add("")
    add("## Pareto front (tensile vs MFR, posterior means)")
    add("")
    add("| rank | matrix | filler wt% | additive_a wt% | additive_b wt% | matrix wt% | tensile pred MPa | MFR pred | P(MFR ok) |")
    add("|---|---|---|---|---|---|---|---|---|")
    for item in pareto:
        add(
            f"| {item['rank']} | {item['matrix_grade']} | {item['filler_wt_pct']} | {item['additive_a_wt_pct']} | "
            f"{item['additive_b_wt_pct']} | {item['matrix_wt_pct']} | {item['tensile_pred_MPa']} | "
            f"{item['mfr_pred_g_per_10min']} | {item['p_mfr_feasible']:.0%} |"
        )
    add("")
    add("## Simulated closed loop (propose -> synthetic oracle -> refit)")
    add("")
    add("| round | matrix | filler wt% | tensile pred | sd | tensile observed | MFR observed |")
    add("|---|---|---|---|---|---|---|")
    for item in history:
        add(
            f"| {item['round']} | {item['matrix_grade']} | {item['filler_wt_pct']} | {item['pred_tensile_MPa']} | "
            f"{item['pred_sd_MPa']} | {item['observed_tensile_MPa']} | {item['observed_mfr']} |"
        )
    add("")
    add("Each round proposes the best feasible candidate (P(MFR ok) >= threshold) and then")
    add("queries the synthetic oracle. The oracle is the same generator used to create the")
    add("dataset, so the loop validates the plumbing (proposal, uncertainty, refit), not")
    add("real predictive skill.")
    add("")
    add("## Claim labels")
    add("")
    add("| label | meaning |")
    add("|---|---|")
    for label, meaning in CLAIM_LABELS:
        add(f"| {label} | {meaning} |")
    add("")
    add("Rules used in this example:")
    add("")
    add("1. Only measured values may be reported as results.")
    add("2. Predicted values always carry mean and sd; never a bare number.")
    add("3. Exploratory candidates are screening suggestions; they become predictions after")
    add("   a model check and measured values after experiments.")
    add("4. Exploration screening range != statistical confidence interval.")
    add("5. Grouped splits are mandatory when samples share a project/batch.")
    add("6. Mass-fraction closure is enforced for data and candidates.")
    add("")
    add("## What this example does NOT claim")
    add("")
    add("- It does not demonstrate property prediction for any real material: the data is synthetic")
    add("  and the surfaces are simple by construction.")
    add("- The GP scores do not transfer to any real formulation dataset.")
    add("- Independent single-output GPs ignore output correlations; a multi-task GP or")
    add("  joint multi-objective acquisition (qEHVI) is out of scope here.")
    add("- The surrogate ranking is not proven better than an experienced engineer's DOE")
    add("  intuition; that requires a real experimental loop.")
    add("")
    add(f"Run mode: {'quick (CI)' if quick else 'full'}.")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic small-data materials ML demo")
    parser.add_argument("--quick", action="store_true", help="small pool and one active-learning round")
    parser.add_argument("--regenerate", action="store_true", help="regenerate the synthetic dataset first")
    parser.add_argument("--priors", default=None, help="CSV with feature,min,max bounds from literature")
    args = parser.parse_args()
    warnings.filterwarnings("ignore", category=ConvergenceWarning)

    if args.regenerate or not DATA_FILE.exists():
        write_synthetic(build_rows())
        print(f"generated synthetic dataset -> {DATA_FILE}")

    rows = load_rows()
    sources = {row.get("data_source", "") for row in rows}
    if sources != {"synthetic"}:
        raise SystemExit(f"refusing to run: expected only synthetic data, found {sorted(sources)}")
    assert_closed(rows)

    bounds = dict(DEFAULT_BOUNDS)
    priors = []
    if args.priors:
        bounds, priors = load_priors(args.priors, bounds)
        print(f"priors applied: {len(priors)} feature bound(s) from {args.priors}")

    rng = np.random.default_rng(SEED)
    pool_size = 400 if args.quick else 2000
    rounds = 1 if args.quick else 3

    metrics = [logo_validation(rows, target) for target in TARGETS]
    for item in metrics:
        print(
            f"LOGO {item['target']}: GP R2={item['r2_gp']:+.2f} RMSE={item['rmse_gp']:.3f} "
            f"coverage 1s={item['coverage_1s']:.0%}"
        )

    calibration = {target: anchored_logo(rows, target) for target in TARGETS}
    for target in TARGETS:
        row = calibration[target]
        print(
            f"CAL {target}: 1s coverage zero-shot={row[0]['coverage_1s']:.0%} "
            f"1-anchor={row[1]['coverage_1s']:.0%} 2-anchor={row[2]['coverage_1s']:.0%}"
        )

    ard = ard_length_scales(fit_target(rows, "tensile_MPa"))
    corr_names, corr_matrix = output_correlations(rows)

    recommendation = recommend(rows, candidate_pool(pool_size, rng, bounds))
    pareto = pareto_candidates(rows, candidate_pool(pool_size, rng, bounds))
    history = active_learning(rows, rounds, pool_size // 2, rng, bounds)

    OUT.mkdir(parents=True, exist_ok=True)
    write_rows(OUT / "logo_metrics.csv", metrics)
    write_rows(
        OUT / "calibration.csv",
        [item for target in TARGETS for item in calibration[target].values()],
    )
    write_rows(OUT / "candidates.csv", recommendation["picked"], CANDIDATE_FIELDS)
    write_rows(OUT / "pareto.csv", pareto, PARETO_FIELDS)
    write_rows(OUT / "active_learning.csv", history)
    (OUT / "report.md").write_text(
        build_report(rows, metrics, calibration, recommendation, pareto, history,
                     bounds, priors, ard, (corr_names, corr_matrix), args.quick),
        encoding="utf-8",
    )

    print()
    print(f"feasible candidates: {recommendation['n_feasible']}")
    print("ECI top-3 (all candidates):")
    for item in recommendation["picked"][:3]:
        print(
            f"  #{item['rank']} matrix {item['matrix_grade']} filler {item['filler_wt_pct']} wt% "
            f"-> tensile {item['tensile_pred_MPa']} +/- {item['tensile_sd_MPa']} MPa, "
            f"P(MFR ok)={item['p_mfr_feasible']:.0%}, ECI={item['eci']}"
        )
    print("feasible top-3 (P(MFR ok) >= threshold):")
    for item in recommendation["picked_feasible"][:3]:
        print(
            f"  #{item['rank']} matrix {item['matrix_grade']} filler {item['filler_wt_pct']} wt% "
            f"-> tensile {item['tensile_pred_MPa']} +/- {item['tensile_sd_MPa']} MPa, "
            f"P(MFR ok)={item['p_mfr_feasible']:.0%}, ECI={item['eci']}"
        )
    for item in history:
        print(
            f"  round {item['round']}: predicted {item['pred_tensile_MPa']} +/- {item['pred_sd_MPa']} MPa, "
            f"observed {item['observed_tensile_MPa']} MPa"
        )
    print()
    print(f"outputs written to {OUT}")
    print("REMINDER: synthetic data only; predictions are not material data.")


if __name__ == "__main__":
    main()
