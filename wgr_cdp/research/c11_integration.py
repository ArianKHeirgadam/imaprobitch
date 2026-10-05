"""C-11: end-to-end research-run integration and artifact contract.

This module audits the concrete CLI research run after A0-A8/C-09/C-10
execution. It does not fabricate scientific evidence: missing empirical values
remain data-dependent, while missing required software artifacts fail the
integration gate.

C-11 is intentionally an orchestration/audit layer. The legacy lightweight
pipeline runner remains backward compatible and is not treated as the real
research execution path.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

UNAVAILABLE = "Data unavailable"
SCHEMA_VERSION = "c11.integration.v1"

REQUIRED_ARTIFACT_GROUPS = {
    "base_analysis": (
        "variants/variants.csv",
        "variants/significant_variants.csv",
        "variants/genes.csv",
        "variants/significant_genes.csv",
        "variants/candidates.csv",
        "variants/summary.json",
        "variants/annotations.json",
        "variants/run.json",
        "report.html",
    ),
    "a5_evidence": (
        "candidate_evidence.csv",
        "candidate_constraints.json",
        "ranking_sensitivity.json",
        "literature_whitespace.json",
        "c10_literature_evidence.json",
        "c10_literature_evidence.csv",
    ),
    "a6_validation": (
        "a6_validation.json",
        "a6_baseline_comparison.json",
        "a6_bootstrap_stability.json",
        "a6_ablation.csv",
    ),
    "a7_panel": (
        "final_panel.json",
        "final_panel_candidates.csv",
        "final_panel_constraints.json",
        "final_panel_diagnostics.json",
    ),
    "a8_validation": (
        "a8_validation.json",
        "a8_leakage_audit.json",
        "a8_bootstrap_stability.json",
        "a8_generalization.json",
        "a8_generalization.csv",
        "a8_quality_gate.json",
    ),
    "c09_robustness": (
        "c09_robustness.json",
        "c09_weight_sensitivity.csv",
        "c09_threshold_sensitivity.csv",
        "c09_k_sensitivity.csv",
        "c09_missingness_stress.csv",
    ),
}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _nonempty(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def _csv_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _artifact_record(root: Path, relative: str) -> dict:
    path = root / relative
    return {
        "path": relative,
        "exists": path.exists(),
        "nonempty": _nonempty(path),
        "status": "Available" if _nonempty(path) else "FAIL",
    }


def _group_status(records: Iterable[dict]) -> str:
    rows = list(records)
    return "Available" if rows and all(r["status"] == "Available" for r in rows) else "FAIL"


def audit_run_artifacts(output_dir) -> dict:
    """Audit required artifacts and cross-stage consistency of one run."""
    root = Path(output_dir)
    groups = {}
    flat = []
    for group, paths in REQUIRED_ARTIFACT_GROUPS.items():
        records = [_artifact_record(root, rel) for rel in paths]
        groups[group] = {
            "status": _group_status(records),
            "required_count": len(records),
            "present_count": sum(bool(r["exists"]) for r in records),
            "artifacts": records,
        }
        flat.extend(records)

    checks = []

    def check(name, passed, detail):
        checks.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        })

    required_ok = all(item["status"] == "Available" for item in groups.values())
    check(
        "required_artifacts",
        required_ok,
        "All mandatory C-11 upstream artifacts exist and are non-empty."
        if required_ok else
        "At least one mandatory upstream artifact is missing or empty.",
    )

    a5_count_ok = False
    a5_detail = UNAVAILABLE
    try:
        constraints = _json(root / "candidate_constraints.json")
        expected = sum(int(constraints.get(key, 0)) for key in ("ranked", "ineligible", "unscored"))
        observed = _csv_count(root / "candidate_evidence.csv")
        a5_count_ok = observed >= 0 and observed == expected
        a5_detail = f"candidate_evidence rows={observed}; partition total={expected}"
    except Exception as exc:
        a5_detail = f"candidate evidence contract unreadable: {type(exc).__name__}"
    check("a5_candidate_partition", a5_count_ok, a5_detail)

    c10_ok = False
    c10_detail = UNAVAILABLE
    try:
        payload = _json(root / "c10_literature_evidence.json")
        records = payload.get("records", [])
        observed = _csv_count(root / "c10_literature_evidence.csv")
        c10_ok = (
            payload.get("schema_version") == "c10.literature.v1"
            and isinstance(records, list)
            and observed == len(records)
            and set(payload.get("sources", [])) <= {"PubMed", "Europe PMC"}
        )
        c10_detail = f"schema={payload.get('schema_version')}; JSON records={len(records)}; CSV rows={observed}"
    except Exception as exc:
        c10_detail = f"C-10 artifact contract unreadable: {type(exc).__name__}"
    check("c10_literature_contract", c10_ok, c10_detail)

    a7_ok = False
    a7_detail = UNAVAILABLE
    try:
        panel = _json(root / "final_panel.json")
        panel_data = panel.get("panel", {})
        selected = panel_data.get("selected", [])
        max_k = int(panel_data.get("max_k", 15))
        a7_ok = len(selected) <= 15 and len(selected) <= max_k <= 15
        a7_detail = f"selected={len(selected)}; max_k={max_k}"
    except Exception as exc:
        a7_detail = f"A7 panel artifact unreadable: {type(exc).__name__}"
    check("a7_panel_cap", a7_ok, a7_detail)

    c09_ok = False
    c09_detail = UNAVAILABLE
    try:
        payload = _json(root / "c09_robustness.json")
        c09_ok = payload.get("schema_version") == "c09.robustness.v1"
        c09_detail = f"schema={payload.get('schema_version')}"
    except Exception as exc:
        c09_detail = f"C-09 artifact unreadable: {type(exc).__name__}"
    check("c09_schema", c09_ok, c09_detail)

    a8_ok = False
    a8_detail = UNAVAILABLE
    try:
        gate = _json(root / "a8_quality_gate.json")
        overall = gate.get("overall")
        a8_ok = overall in {"PASS", "CONDITIONAL", "FAIL"}
        a8_detail = f"quality_gate={overall}"
    except Exception as exc:
        a8_detail = f"A8 quality gate unreadable: {type(exc).__name__}"
    check("a8_quality_gate_contract", a8_ok, a8_detail)

    report_ok = _nonempty(root / "report.html")
    check(
        "report_present",
        report_ok,
        "HTML report exists and is non-empty." if report_ok else "HTML report missing or empty.",
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if required_ok and all(c["status"] == "PASS" for c in checks) else "FAIL",
        "groups": groups,
        "checks": checks,
        "artifact_count": len(flat),
        "available_artifact_count": sum(r["status"] == "Available" for r in flat),
        "scientific_boundary": (
            "C-11 validates software integration, artifact completeness and "
            "cross-stage contracts. It does not convert generated outputs into "
            "biological, clinical, or independent-validation claims."
        ),
    }


def build_c11_manifest(output_dir, config=None, run_id=None) -> dict:
    """Build an auditable C-11 manifest before the final A9 hash pass."""
    root = Path(output_dir)
    audit = audit_run_artifacts(root)
    validation_config = (config or {}).get("validation_candidates")

    optional_inputs = {
        "multimodal": _nonempty(root / "multimodal" / "multimodal_cohort_comparison.csv"),
        "cnv": _nonempty(root / "cnv" / "cnv_candidates.csv"),
        "independent_validation": (
            bool(validation_config) and Path(str(validation_config)).exists()
        ),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": str(run_id or UNAVAILABLE),
        "status": audit["status"],
        "execution_contract": [
            "base_analysis",
            "a5_evidence",
            "a6_validation",
            "a7_panel",
            "a8_validation",
            "c09_robustness",
            "c10_literature",
            "c11_integration",
            "a9_reproducibility",
        ],
        "dependency_graph": {
            "base_analysis": [],
            "a5_evidence": ["base_analysis"],
            "a6_validation": ["a5_evidence"],
            "a7_panel": ["a5_evidence"],
            "a8_validation": ["a7_panel", "a5_evidence"],
            "c09_robustness": ["a5_evidence", "a7_panel"],
            "c10_literature": ["a5_evidence"],
            "c11_integration": [
                "base_analysis", "a5_evidence", "a6_validation",
                "a7_panel", "a8_validation", "c09_robustness", "c10_literature"
            ],
            "a9_reproducibility": ["c11_integration"],
        },
        "config": dict(config or {}),
        "optional_inputs_observed": optional_inputs,
        "audit": audit,
    }


def write_c11_artifacts(output_dir, config=None, run_id=None) -> dict:
    """Write the C-11 integration manifest and compact artifact index."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest = build_c11_manifest(root, config=config, run_id=run_id)

    manifest_path = root / "c11_integration_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str),
        encoding="utf-8",
    )

    index_path = root / "c11_artifact_index.csv"
    rows = []
    for group, payload in manifest["audit"]["groups"].items():
        for artifact in payload["artifacts"]:
            rows.append({
                "group": group,
                "path": artifact["path"],
                "exists": artifact["exists"],
                "nonempty": artifact["nonempty"],
                "status": artifact["status"],
            })
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["group", "path", "exists", "nonempty", "status"],
        )
        writer.writeheader()
        writer.writerows(rows)

    return {
        "status": manifest["status"],
        "schema_version": SCHEMA_VERSION,
        "manifest": str(manifest_path),
        "artifact_index": str(index_path),
        "required_artifact_count": manifest["audit"]["artifact_count"],
        "available_artifact_count": manifest["audit"]["available_artifact_count"],
    }


def append_c11_to_report(output_dir, result) -> bool:
    """Append C-11 integration status to the existing HTML report."""
    report_path = Path(output_dir) / "report.html"
    if not report_path.exists():
        return False

    import html

    manifest = result.get("manifest", "c11_integration_manifest.json")
    section = (
        "<hr><h2>C-11 End-to-End Integration Gate</h2>"
        "<p>C-11 verifies software-level stage dependencies and required artifacts; "
        "it is not a biological or clinical validation claim.</p>"
        f"<ul><li>Integration status: <strong>{html.escape(str(result.get('status', 'Data unavailable')))}</strong></li>"
        f"<li>Required artifacts available: {int(result.get('available_artifact_count', 0))}/"
        f"{int(result.get('required_artifact_count', 0))}</li></ul>"
        "<p>Machine-readable C-11 artifacts: "
        f"<code>{html.escape(Path(manifest).name)}</code>, "
        "<code>c11_artifact_index.csv</code>.</p>"
    )
    document = report_path.read_text(encoding="utf-8")
    marker = "</body>"
    document = document.replace(marker, section + marker, 1) if marker in document else document + section
    report_path.write_text(document, encoding="utf-8")
    return True
