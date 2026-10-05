"""A12 real GDC case/sample/file cohort construction.

This layer builds an analysis manifest from GDC metadata. It never converts
project-level counts into sample counts and never infers tumor/normal status
from filenames. Cohort eligibility is based on explicit GDC sample metadata.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

from .gdc import GDC_API, GDCIntakeError


def _post_json(endpoint: str, payload: dict, timeout: int = 30) -> dict:
    body = json.dumps(payload).encode("utf-8")
    url = f"{GDC_API}/{endpoint.lstrip('/')}"
    last_exc = None
    for attempt in range(3):
        request = Request(
            url,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Connection": "close",
                "User-Agent": "WGR-CDP/1.4",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
    raise GDCIntakeError(
        f"GDC cohort query failed after 3 attempts: {type(last_exc).__name__}"
    ) from last_exc


def query_cases(project_id: str, *, size: int = 5000, timeout: int = 30) -> list[dict]:
    if size < 1 or size > 5000:
        raise ValueError("size must be between 1 and 5000")
    fields = ",".join([
        "case_id", "submitter_id", "project.project_id",
        "samples.sample_id", "samples.submitter_id", "samples.sample_type",
        "samples.tissue_type", "samples.tumor_descriptor",
        "samples.preservation_method", "samples.is_ffpe",
        "samples.portions.analytes.aliquots.aliquot_id",
        "diagnoses.primary_diagnosis", "diagnoses.tissue_source_site",
    ])
    filters = {"op": "in", "content": {"field": "project.project_id", "value": [project_id]}}
    out = []
    offset = 0
    while True:
        payload = {"filters": filters, "fields": fields, "format": "JSON",
                   "size": size, "from": offset}
        response = _post_json("cases", payload, timeout=timeout)
        data = response.get("data") or {}
        hits = data.get("hits") if isinstance(data.get("hits"), list) else []
        out.extend(hits)
        pagination = data.get("pagination") or {}
        total = pagination.get("total")
        if not hits or total is None or (isinstance(total, int) and offset + len(hits) >= total):
            return out
        offset += len(hits)


def query_variant_files(project_id: str, *, access: str | None = None,
                        size: int = 5000, timeout: int = 30) -> list[dict]:
    if size < 1 or size > 5000:
        raise ValueError("size must be between 1 and 5000")
    content = [{"op": "in", "content": {
        "field": "cases.project.project_id", "value": [project_id]
    }}]
    if access:
        content.append({"op": "in", "content": {
            "field": "access", "value": [access]
        }})
    filters = {"op": "and", "content": content}
    fields = ",".join([
        "file_id", "file_name", "file_size", "md5sum",
        "data_category", "data_type", "data_format", "access",
        "experimental_strategy", "analysis.workflow_type",
        "analysis.workflow_version", "cases.case_id", "cases.submitter_id",
        "cases.samples.sample_id", "cases.samples.submitter_id",
        "cases.samples.sample_type", "cases.samples.tissue_type",
        "cases.samples.tumor_descriptor",
    ])
    out = []
    offset = 0
    while True:
        payload = {"filters": filters, "fields": fields, "format": "JSON",
                   "size": size, "from": offset}
        response = _post_json("files", payload, timeout=timeout)
        data = response.get("data") or {}
        hits = data.get("hits") if isinstance(data.get("hits"), list) else []
        for row in hits:
            category = str(row.get("data_category") or "").strip().lower()
            dtype = str(row.get("data_type") or "").strip().lower()
            if category in {"simple nucleotide variation", "structural variation"} or "variant" in category or "mutation" in dtype:
                out.append(row)
        pagination = data.get("pagination") or {}
        total = pagination.get("total")
        if not hits or total is None or (isinstance(total, int) and offset + len(hits) >= total):
            return out
        offset += len(hits)


def _sample_rows(case: dict) -> list[dict]:
    samples = case.get("samples") if isinstance(case.get("samples"), list) else []
    rows = []
    for sample in samples:
        rows.append({
            "case_id": case.get("case_id", "Data unavailable"),
            "case_submitter_id": case.get("submitter_id", "Data unavailable"),
            "sample_id": sample.get("sample_id", "Data unavailable"),
            "sample_submitter_id": sample.get("submitter_id", "Data unavailable"),
            "sample_type": sample.get("sample_type", "Data unavailable"),
            "tissue_type": sample.get("tissue_type", "Data unavailable"),
            "tumor_descriptor": sample.get("tumor_descriptor", "Data unavailable"),
            "preservation_method": sample.get("preservation_method", "Data unavailable"),
            "is_ffpe": sample.get("is_ffpe", "Data unavailable"),
        })
    return rows


def classify_sample(sample: dict) -> str:
    """Classify only from explicit GDC sample metadata."""
    sample_type = str(sample.get("sample_type") or "").lower()
    tissue_type = str(sample.get("tissue_type") or "").lower()
    descriptor = str(sample.get("tumor_descriptor") or "").lower()
    if "solid tissue normal" in sample_type or tissue_type == "normal":
        return "NORMAL"
    if "primary tumor" in sample_type or "recurrent tumor" in sample_type:
        return "TUMOR"
    if "metastatic" in sample_type:
        return "TUMOR_METASTATIC"
    if "tumor" in descriptor:
        return "TUMOR"
    return "UNCLASSIFIED"


def build_cohort_manifest(project_id: str, cases: list[dict],
                          variant_files: list[dict] | None = None) -> dict:
    samples = []
    seen = set()
    for case in cases:
        for row in _sample_rows(case):
            key = (row["case_id"], row["sample_id"])
            if key in seen:
                continue
            seen.add(key)
            row["sample_class"] = classify_sample(row)
            row["exclusion_reasons"] = []
            if row["sample_class"] == "UNCLASSIFIED":
                row["exclusion_reasons"].append("sample_class_unclassified")
            samples.append(row)

    file_rows = []
    for row in variant_files or []:
        item = dict(row)
        item["analysis_status"] = "metadata_only"
        item["local_path"] = None
        item["genome_build"] = "Data unavailable"
        item["sample_mapping_status"] = "Available" if (
            row.get("cases") or row.get("case_id")
        ) else "Data unavailable"
        file_rows.append(item)

    tumors = [s for s in samples if s["sample_class"] in {"TUMOR", "TUMOR_METASTATIC"}]
    normals = [s for s in samples if s["sample_class"] == "NORMAL"]
    excluded = [s for s in samples if s["exclusion_reasons"]]
    return {
        "schema_version": "A12-1",
        "status": "Available" if samples else "Data unavailable",
        "project_id": project_id,
        "sample_count": len(samples),
        "tumor_sample_count": len(tumors),
        "normal_sample_count": len(normals),
        "excluded_sample_count": len(excluded),
        "case_count_observed": len({s["case_id"] for s in samples}),
        "samples": sorted(samples, key=lambda x: (str(x["case_id"]), str(x["sample_id"]))),
        "variant_files": sorted(file_rows, key=lambda x: str(x.get("file_id", ""))),
        "analysis_ready": False,
        "analysis_ready_reason": "local_file_acquisition_genome_build_and_sample_level_qc_required",
        "biological_results": "Data unavailable",
    }


def write_cohort_manifest(output: str | Path, manifest: dict) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path
