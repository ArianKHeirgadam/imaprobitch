"""Study-level TCGA cohort selection for Cancer-vs-Normal analysis.

The selector works at case/sample level and distinguishes paired non-tumor
samples from unrelated population references. It never calls a TCGA normal
sample an independent healthy population.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json

UNAVAILABLE = "Data unavailable"

def _sample_class(sample):
    sample_type = str(sample.get("sample_type") or "").strip().lower()
    tissue_type = str(sample.get("tissue_type") or "").strip().lower()
    descriptor = str(sample.get("tumor_descriptor") or "").strip().lower()
    if sample_type == "primary tumor" or "primary tumor" in sample_type:
        return "TUMOR"
    if sample_type == "recurrent tumor" or "recurrent tumor" in sample_type:
        return "TUMOR"
    if sample_type == "blood derived normal" or "blood derived normal" in sample_type:
        return "NORMAL_BLOOD"
    if sample_type == "solid tissue normal" or "solid tissue normal" in sample_type:
        return "NORMAL_SOLID"
    if tissue_type == "normal":
        return "NORMAL_SOLID"
    if "tumor" in descriptor:
        return "TUMOR"
    return "UNCLASSIFIED"

def select_paired_tcga_cases(cohort_manifest, normal_preference=("NORMAL_SOLID", "NORMAL_BLOOD")):
    samples = cohort_manifest.get("samples") or []
    by_case = defaultdict(list)
    for sample in samples:
        case = str(sample.get("case_id") or "")
        if case:
            item = dict(sample)
            item["selected_class"] = _sample_class(item)
            by_case[case].append(item)

    selected = []
    excluded = []
    for case_id, case_samples in sorted(by_case.items()):
        tumors = [s for s in case_samples if s["selected_class"] == "TUMOR"]
        normals = [s for s in case_samples if s["selected_class"] in normal_preference]
        if not tumors or not normals:
            excluded.append({
                "case_id": case_id,
                "reason": "no_explicit_tumor_normal_pair",
                "tumor_count": len(tumors),
                "normal_count": len(normals),
            })
            continue
        tumor = sorted(tumors, key=lambda s: str(s.get("sample_id", "")))[0]
        normal_rank = {
            kind: index for index, kind in enumerate(normal_preference)
        }
        normal = sorted(
            normals,
            key=lambda s: (
                normal_rank.get(s["selected_class"], 999),
                str(s.get("sample_id", "")),
            ),
        )[0]
        selected.append({
            "case_id": case_id,
            "tumor_sample": tumor,
            "normal_sample": normal,
            "pair_status": "PAIRED",
        })

    return {
        "schema_version": "A12-STUDY-COHORT-1",
        "status": "Available" if selected else UNAVAILABLE,
        "source_project": cohort_manifest.get("project_id", UNAVAILABLE),
        "selection_rule": (
            "Select cases with one explicit tumor sample and one explicit normal "
            "sample from the same case; prefer solid-tissue normal over blood-derived normal."
        ),
        "selected_pair_count": len(selected),
        "selected": selected,
        "excluded_cases": excluded,
        "scientific_roles": {
            "tumor": "Cancer discovery cohort",
            "normal": "Paired non-tumor comparator, not an independent healthy population",
        },
    }

def _file_case_ids(row):
    cases = row.get("cases")
    if isinstance(cases, dict):
        cases = [cases]
    if not isinstance(cases, list):
        cases = []
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            continue
        for key in ("case_id", "submitter_id"):
            value = case.get(key)
            if value:
                ids.add(str(value))
    for key in ("case_id", "submitter_id"):
        value = row.get(key)
        if value:
            ids.add(str(value))
    return ids

def select_variant_files(variant_files, *, modality="SNV_INDEL",
                         access=None, strategy=None, case_ids=None):
    selected = []
    wanted_cases = {str(x) for x in (case_ids or [])}
    for row in variant_files or []:
        row_access = str(row.get("access") or "").lower()
        if access and row_access != str(access).lower():
            continue
        experimental = str(row.get("experimental_strategy") or "").upper()
        if strategy and experimental and experimental != str(strategy).upper():
            continue
        category = str(row.get("data_category") or "").lower()
        data_type = str(row.get("data_type") or "").lower()
        fmt = str(row.get("data_format") or "").upper()
        text = " ".join((category, data_type, fmt))
        if modality == "SNV_INDEL":
            if "mutation" not in text and fmt not in {"MAF", "VCF"}:
                continue
        elif modality == "CNV":
            if "copy number" not in text and "cnv" not in text:
                continue
        else:
            continue
        if wanted_cases and not (wanted_cases & _file_case_ids(row)):
            continue
        selected.append(dict(row))
    selected.sort(key=lambda r: (str(r.get("file_name", "")), str(r.get("file_id", ""))))
    return selected

def select_open_variant_files(variant_files, *, modality="SNV_INDEL", strategy="WXS"):
    return select_variant_files(
        variant_files, modality=modality, access="open", strategy=strategy
    )

    for row in variant_files or []:
        access = str(row.get("access") or "").lower()
        experimental = str(row.get("experimental_strategy") or "").upper()
        category = str(row.get("data_category") or "").lower()
        data_type = str(row.get("data_type") or "").lower()
        fmt = str(row.get("data_format") or "").upper()
        text = " ".join((category, data_type, fmt))
        if access != "open":
            continue
        if modality == "SNV_INDEL":
            if "mutation" not in text and fmt not in {"MAF", "VCF"}:
                continue
            if strategy and experimental and experimental != strategy.upper():
                continue
        elif modality == "CNV":
            if "copy number" not in text and "cnv" not in text:
                continue
        else:
            continue
        selected.append(dict(row))
    selected.sort(key=lambda r: (str(r.get("file_name", "")), str(r.get("file_id", ""))))
    return selected

def write_study_selection(path, selection):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(selection, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _file_rank(row, modality):
    workflow = str((row.get("analysis") or {}).get("workflow_type") or row.get("workflow_type") or "").lower()
    data_type = str(row.get("data_type") or "").lower()
    name = str(row.get("file_name") or "").lower()
    if modality == "SNV_INDEL":
        return (
            0 if "gatk4 mutect2 pair" in workflow else
            1 if "gatk4 mutect2" in workflow else
            2 if "mutect2" in workflow else
            3 if "varscan2" in workflow else
            4 if "svaba" in workflow else 9,
            0 if "annotated somatic mutation" in data_type else
            1 if "raw simple somatic mutation" in data_type else 9,
            name,
            str(row.get("file_id", "")),
        )
    return (
        0 if "allele-specific copy number segment" in data_type else
        1 if "copy number segment" in data_type else 2,
        0 if "ascat" in workflow else
        1 if "facets" in workflow else 2,
        name,
        str(row.get("file_id", "")),
    )

def select_primary_variant_files(variant_files, *, modality="SNV_INDEL",
                                 access=None, strategy=None, case_ids=None):
    """Select at most one deterministic primary file per paired case.

    Alternative callers remain discoverable in the upstream inventory, but
    downstream discovery uses one primary representation per case to avoid
    double-counting the same biological sample across callers.
    """
    candidates = select_variant_files(
        variant_files,
        modality=modality,
        access=access,
        strategy=strategy,
        case_ids=case_ids,
    )
    wanted_cases = {str(x) for x in (case_ids or [])}
    grouped = defaultdict(list)
    for row in candidates:
        ids = _file_case_ids(row)
        if wanted_cases:
            ids &= wanted_cases
        for case_id in ids:
            grouped[str(case_id)].append(row)
    selected = []
    for case_id in sorted(grouped):
        selected.append(dict(min(
            grouped[case_id],
            key=lambda row: _file_rank(row, modality),
        )))
    return selected


def select_open_study_subset(study_manifest, limit=20, *, strategy="WXS"):
    """Select a deterministic paired-case subset from the open WXS fallback.

    The limit applies to biological cases, not arbitrary files. Only paired
    TCGA cases that have an open WXS SNV/INDEL MAF/VCF representation are
    eligible. The subset is for real-data software validation and does not
    imply whole-cohort statistical inference.
    """
    limit = int(limit)
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    paired = study_manifest.get("selected") or []
    paired_ids = {
        str(item.get("case_id"))
        for item in paired
        if item.get("case_id")
    }
    public = []
    for row in study_manifest.get("public_wxs_maf_fallback") or []:
        if str(row.get("access") or "").lower() != "open":
            continue
        if str(row.get("experimental_strategy") or "").upper() != str(strategy).upper():
            continue
        fmt = str(row.get("data_format") or "").upper()
        if fmt not in {"MAF", "VCF"}:
            continue
        case_ids = _file_case_ids(row)
        eligible = sorted(case_ids & paired_ids)
        if not eligible:
            continue
        item = dict(row)
        item["_eligible_case_ids"] = eligible
        public.append(item)

    by_case = defaultdict(list)
    for row in public:
        for case_id in row["_eligible_case_ids"]:
            by_case[case_id].append(row)

    selected_cases = []
    selected_files = []
    for case_id in sorted(by_case):
        if len(selected_cases) >= limit:
            break
        row = min(
            by_case[case_id],
            key=lambda item: (
                str(item.get("file_name") or ""),
                str(item.get("file_id") or ""),
            ),
        )
        selected_cases.append(case_id)
        item = dict(row)
        item.pop("_eligible_case_ids", None)
        item["study_role"] = "public_wxs_subset"
        selected_files.append(item)

    return {
        "schema_version": "A13-STUDY-SUBSET-1",
        "status": "Available" if selected_files else UNAVAILABLE,
        "source_project": study_manifest.get("source_project", UNAVAILABLE),
        "requested_case_limit": limit,
        "selected_case_count": len(selected_cases),
        "selected_file_count": len(selected_files),
        "selected_case_ids": selected_cases,
        "selected_files": selected_files,
        "full_paired_case_count": int(study_manifest.get("selected_pair_count") or 0),
        "full_open_public_wxs_count": len(public),
        "selection_rule": (
            "Deterministic lexical case ordering; one open WXS SNV/INDEL "
            "MAF/VCF representation per eligible paired case."
        ),
        "access_policy": "open_only",
        "download_scope": "subset_only",
        "scientific_role": (
            "Real-data subset validation; not a whole-cohort statistical result "
            "and not an independent healthy population."
        ),
    }
