"""Leakage-safe validation primitives and reproducibility guards.

C-04 extends the existing A6/A8 helpers with explicit patient-level
partitioning, split manifests, missing-label-safe evaluation, and a frozen
fit/evaluate boundary. These are research/evaluation utilities and do not
imply clinical validity.
"""
from __future__ import annotations

from collections import defaultdict
from enum import Enum
import json
from pathlib import Path
from random import Random
from typing import Any, Iterable, Mapping, Sequence


UNKNOWN_LABELS = {
    "", "unknown", "missing", "unavailable", "data unavailable", "na", "n/a",
    "none", "null", "not available",
}
POSITIVE_LABELS = {"1", "positive", "present", "detected", "case", "cancer", "yes", "true"}
NEGATIVE_LABELS = {"0", "negative", "absent", "not detected", "not_detected", "control", "healthy", "no", "false"}


class AnalysisState(str, Enum):
    DISCOVERY = "DISCOVERY"
    FROZEN = "FROZEN"
    VALIDATION = "VALIDATION"


class LeakageGuard:
    def __init__(self):
        self.state = AnalysisState.DISCOVERY

    def freeze(self):
        self.state = AnalysisState.FROZEN

    def enter_validation(self):
        if self.state != AnalysisState.FROZEN:
            raise RuntimeError("validation requires a frozen analysis")
        self.state = AnalysisState.VALIDATION

    def require(self, state):
        if self.state != state:
            raise RuntimeError(
                f"operation requires {state.value}, current state is {self.state.value}"
            )


def bootstrap_selection(samples, selector, n_bootstrap=200, seed=42):
    rng = Random(seed)
    samples = list(samples)
    counts = {}
    if not samples:
        return counts
    for _ in range(n_bootstrap):
        draw = [samples[rng.randrange(len(samples))] for _ in samples]
        for candidate in selector(draw):
            counts[candidate] = counts.get(candidate, 0) + 1
    return {candidate: n / n_bootstrap for candidate, n in counts.items()}


def cohort_holdout_guard(discovery_ids, validation_ids):
    overlap = set(discovery_ids) & set(validation_ids)
    if overlap:
        raise ValueError(f"cohort leakage detected: {sorted(overlap)}")
    return True


def patient_level_split(patient_ids, validation_fraction=0.2, test_fraction=0.2, seed=42):
    """Deterministically split unique patients; no patient can cross partitions."""
    ids = sorted({str(x) for x in patient_ids if x not in (None, "")})
    vf = float(validation_fraction)
    tf = float(test_fraction)
    if vf < 0 or tf < 0 or vf + tf >= 1:
        raise ValueError("validation_fraction + test_fraction must be in [0, 1)")
    rng = Random(seed)
    rng.shuffle(ids)
    n = len(ids)
    n_test = int(n * tf)
    n_validation = int(n * vf)
    test = ids[:n_test]
    validation = ids[n_test:n_test + n_validation]
    discovery = ids[n_test + n_validation:]
    return {
        "discovery": discovery,
        "validation": validation,
        "test": test,
        "seed": int(seed),
        "counts": {
            "discovery": len(discovery),
            "validation": len(validation),
            "test": len(test),
        },
    }


def _row_patient(row: Mapping[str, Any]) -> str:
    for key in ("patient_id", "patient", "subject_id", "subject", "participant_id"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _row_label(row: Mapping[str, Any]) -> Any:
    for key in ("label", "class", "outcome", "target", "status"):
        if key in row:
            return row.get(key)
    return None


def _normalize_label(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in UNKNOWN_LABELS:
        return None
    if text in POSITIVE_LABELS:
        return 1
    if text in NEGATIVE_LABELS:
        return 0
    try:
        numeric = int(float(text))
    except (TypeError, ValueError):
        return None
    return numeric if numeric in (0, 1) else None


def audit_three_way_split(discovery_ids, validation_ids, test_ids):
    """Require mutually disjoint, explicitly populated patient cohorts."""
    cohorts = {
        "discovery": {str(x) for x in discovery_ids if x not in (None, "")},
        "validation": {str(x) for x in validation_ids if x not in (None, "")},
        "test": {str(x) for x in test_ids if x not in (None, "")},
    }
    overlaps = {}
    names = list(cohorts)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            overlap = sorted(cohorts[left] & cohorts[right])
            if overlap:
                overlaps[f"{left}__{right}"] = overlap
    complete = all(cohorts.values())
    return {
        "status": "FAIL" if overlaps else ("Available" if complete else "Data unavailable"),
        "leakage_free": bool(not overlaps and complete),
        "counts": {name: len(values) for name, values in cohorts.items()},
        "overlaps": overlaps,
    }


def stratified_patient_level_split(
    rows: Sequence[Mapping[str, Any]],
    validation_fraction=0.2,
    test_fraction=0.2,
    seed=42,
    label_key=None,
):
    """Split patients with optional patient-level binary-label stratification.

    A patient contributes at most one label. Conflicting labels are treated as
    unknown for stratification. Unknown labels never become negatives.
    """
    vf = float(validation_fraction)
    tf = float(test_fraction)
    if vf < 0 or tf < 0 or vf + tf >= 1:
        raise ValueError("validation_fraction + test_fraction must be in [0, 1)")

    labels_by_patient = defaultdict(set)
    all_patients = set()
    for row in rows:
        patient = _row_patient(row)
        if not patient:
            continue
        all_patients.add(patient)
        raw = row.get(label_key) if label_key else _row_label(row)
        label = _normalize_label(raw)
        if label is not None:
            labels_by_patient[patient].add(label)

    known = {
        patient: next(iter(labels))
        for patient, labels in labels_by_patient.items()
        if len(labels) == 1
    }
    unknown = sorted(all_patients - set(known))
    groups = {0: [], 1: []}
    for patient, label in known.items():
        groups[label].append(patient)

    rng = Random(seed)
    for values in groups.values():
        values.sort()
        rng.shuffle(values)

    partitions = {"discovery": [], "validation": [], "test": []}
    for label in (0, 1):
        ids = groups[label]
        n_test = int(len(ids) * tf)
        n_validation = int(len(ids) * vf)
        partitions["test"].extend(ids[:n_test])
        partitions["validation"].extend(ids[n_test:n_test + n_validation])
        partitions["discovery"].extend(ids[n_test + n_validation:])

    rng.shuffle(unknown)
    n_test = int(len(unknown) * tf)
    n_validation = int(len(unknown) * vf)
    partitions["test"].extend(unknown[:n_test])
    partitions["validation"].extend(unknown[n_test:n_test + n_validation])
    partitions["discovery"].extend(unknown[n_test + n_validation:])

    for values in partitions.values():
        values.sort()

    audit = audit_three_way_split(
        partitions["discovery"], partitions["validation"], partitions["test"]
    )
    return {
        **partitions,
        "seed": int(seed),
        "stratified": bool(known),
        "known_label_patients": len(known),
        "unknown_label_patients": len(unknown),
        "counts": {name: len(values) for name, values in partitions.items()},
        "audit": audit,
    }


def build_split_manifest(
    split,
    *,
    seed,
    validation_fraction,
    test_fraction,
    stratified=False,
    label_semantics="unknown labels excluded from class counts; never negative",
):
    """Build a JSON-safe, auditable record of a patient-level split."""
    discovery = sorted({str(x) for x in split.get("discovery", []) if x not in (None, "")})
    validation = sorted({str(x) for x in split.get("validation", []) if x not in (None, "")})
    test = sorted({str(x) for x in split.get("test", []) if x not in (None, "")})
    audit = audit_three_way_split(discovery, validation, test)
    return {
        "schema_version": "c04.split-manifest.v1",
        "unit": "patient",
        "seed": int(seed),
        "validation_fraction": float(validation_fraction),
        "test_fraction": float(test_fraction),
        "stratified": bool(stratified),
        "partitions": {
            "discovery": discovery,
            "validation": validation,
            "test": test,
        },
        "counts": audit["counts"],
        "leakage_audit": audit,
        "label_semantics": label_semantics,
    }


def write_split_manifest(output_path, manifest):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _prediction_rows(rows: Iterable[Mapping[str, Any]], score_key):
    output = []
    patients = set()
    duplicate_patients = set()
    for row in rows:
        patient = _row_patient(row)
        label = _normalize_label(_row_label(row))
        try:
            score = float(row.get(score_key))
        except (TypeError, ValueError):
            score = None
        if patient in patients:
            duplicate_patients.add(patient)
        if patient and label is not None and score is not None:
            patients.add(patient)
            output.append((patient, label, score))
    return output, duplicate_patients


def _roc_auc(labels, scores):
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    if not positives or not negatives:
        return None
    concordant = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                concordant += 1
            elif positive == negative:
                concordant += 0.5
    return concordant / (len(positives) * len(negatives))


def _average_precision(labels, scores):
    positive_n = sum(labels)
    if positive_n == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    hits = 0
    total_precision = 0.0
    for rank, index in enumerate(order, 1):
        if labels[index] == 1:
            hits += 1
            total_precision += hits / rank
    return total_precision / positive_n


def evaluate_binary_predictions(rows, score_key="score", threshold=0.5):
    """Evaluate explicit patient labels only; missing labels are not negatives."""
    observed, duplicate_patients = _prediction_rows(rows, score_key)
    if duplicate_patients:
        return {
            "status": "Data unavailable",
            "reason": "duplicate_patient_predictions_require_patient_level_aggregation",
            "duplicate_patient_ids": sorted(duplicate_patients),
            "n_observed": 0,
            "n_excluded": len(rows),
            "metrics": {},
        }
    if not observed:
        return {
            "status": "Data unavailable",
            "n_observed": 0,
            "n_excluded": len(rows),
            "metrics": {},
        }

    labels = [label for _, label, _ in observed]
    scores = [score for _, _, score in observed]
    predicted = [1 if score >= float(threshold) else 0 for score in scores]
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predicted))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predicted))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predicted))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predicted))
    sensitivity = tp / (tp + fn) if tp + fn else None
    specificity = tn / (tn + fp) if tn + fp else None
    precision = tp / (tp + fp) if tp + fp else None
    recall = sensitivity
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else None
    )
    return {
        "status": "Available",
        "n_observed": len(observed),
        "n_excluded": len(rows) - len(observed),
        "positive_n": sum(labels),
        "negative_n": len(labels) - sum(labels),
        "threshold": float(threshold),
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
        "metrics": {
            "sensitivity": sensitivity,
            "specificity": specificity,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "roc_auc": _roc_auc(labels, scores),
            "pr_auc": _average_precision(labels, scores),
        },
    }


def fit_binary_threshold(rows, score_key="score", objective="f1"):
    """Fit a threshold on discovery data only; never refit on holdout data."""
    observed, duplicate_patients = _prediction_rows(rows, score_key)
    if duplicate_patients:
        return {
            "status": "Data unavailable",
            "reason": "duplicate_patient_predictions_require_patient_level_aggregation",
            "threshold": None,
            "n_observed": 0,
        }
    if not observed:
        return {"status": "Data unavailable", "threshold": None, "n_observed": 0}

    scores = sorted({score for _, _, score in observed})
    candidates = [scores[0]] + [
        (left + right) / 2 for left, right in zip(scores, scores[1:])
    ] + [scores[-1]]
    best = None
    for threshold in candidates:
        evaluation = evaluate_binary_predictions(
            [
                {"patient_id": patient, "label": label, score_key: score}
                for patient, label, score in observed
            ],
            score_key=score_key,
            threshold=threshold,
        )
        value = evaluation["metrics"].get(objective)
        if value is None:
            continue
        key = (float(value), -float(threshold))
        if best is None or key > best[0]:
            best = (key, float(threshold))
    if best is None:
        return {
            "status": "Data unavailable",
            "threshold": None,
            "n_observed": len(observed),
        }
    return {
        "status": "Available",
        "threshold": best[1],
        "objective": str(objective),
        "n_observed": len(observed),
    }


def evaluate_with_frozen_threshold(rows, fitted, score_key="score"):
    """Evaluate a threshold fitted elsewhere without refitting on these rows."""
    if fitted.get("status") != "Available" or fitted.get("threshold") is None:
        return {
            "status": "Data unavailable",
            "reason": "fitted_threshold_unavailable",
            "metrics": {},
        }
    return evaluate_binary_predictions(
        rows, score_key=score_key, threshold=float(fitted["threshold"])
    )
