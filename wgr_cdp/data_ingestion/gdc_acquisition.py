"""A11 GDC inventory, acquisition planning, download and registration.

The module separates discovery from acquisition. Inventory queries may inspect
GDC metadata; biological files are downloaded only when explicitly requested.
Every acquired file is verified against the GDC md5 checksum when available.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .gdc import GDC_API, GDCIntakeError, _get_json


def inventory_files(project_id: str, *, data_category: str | None = None,
                    access: str | None = None, experimental_strategy: str | None = None,
                    data_format: str | None = None, page_size: int = 100,
                    max_files: int | None = None, timeout: int = 30) -> list[dict]:
    """Return a deterministic file inventory for a GDC project."""
    if page_size < 1 or page_size > 5000:
        raise ValueError("page_size must be between 1 and 5000")
    if max_files is not None and max_files < 1:
        raise ValueError("max_files must be positive")
    filters = [{
        "op": "in",
        "content": {"field": "cases.project.project_id", "value": [project_id]},
    }]
    for field, value in (
        ("data_category", data_category),
        ("access", access),
        ("experimental_strategy", experimental_strategy),
        ("data_format", data_format),
    ):
        if value:
            filters.append({"op": "in", "content": {"field": field, "value": [value]}})
    query_fields = ",".join([
        "file_id", "file_name", "file_size", "md5sum", "data_category",
        "data_type", "data_format", "access", "experimental_strategy",
        "cases.project.project_id", "cases.case_id", "cases.submitter_id",
    ])
    out: list[dict] = []
    offset = 0
    while True:
        filters_json = json.dumps({"op": "and", "content": filters}, separators=(",", ":"))
        params = urlencode({
            "filters": filters_json, "fields": query_fields,
            "format": "JSON", "size": str(page_size), "from": str(offset),
        })
        payload = _get_json(f"{GDC_API}/files?{params}", timeout=timeout)
        data = payload.get("data") or {}
        hits = data.get("hits") if isinstance(data.get("hits"), list) else []
        out.extend(hits)
        if max_files is not None and len(out) >= max_files:
            return out[:max_files]
        pagination = data.get("pagination") or {}
        total = pagination.get("total")
        if not hits or (isinstance(total, int) and offset + len(hits) >= total):
            return out
        offset += len(hits)


def classify_file(file_row: dict) -> str:
    category = str(file_row.get("data_category") or "").lower()
    dtype = str(file_row.get("data_type") or "").lower()
    fmt = str(file_row.get("data_format") or "").lower()
    strategy = str(file_row.get("experimental_strategy") or "").lower()
    text = " ".join((category, dtype, fmt, strategy))
    if "variant" in text or fmt in {"vcf", "maf"} or "mutect" in text:
        return "SNV_INDEL"
    if "copy number" in text or "cnv" in text:
        return "CNV"
    if "methyl" in text:
        return "METHYLATION"
    if "structural variant" in text or fmt == "sv":
        return "SV"
    if "clinical" in text:
        return "CLINICAL"
    if "biospecimen" in text:
        return "BIOSPECIMEN"
    return "OTHER"


def build_acquisition_manifest(project_id: str, files: list[dict],
                               selected_types: set[str] | None = None) -> dict:
    selected = []
    for row in files:
        modality = classify_file(row)
        item = dict(row)
        item["modality"] = modality
        item["download_status"] = "planned"
        item["local_path"] = None
        item["verified"] = False
        if selected_types is None or modality in selected_types:
            selected.append(item)
    selected.sort(key=lambda r: (str(r.get("modality")), str(r.get("file_id"))))
    return {
        "schema_version": "A11-1",
        "status": "Available",
        "source": "GDC",
        "project_id": project_id,
        "selected_count": len(selected),
        "selected_modalities": sorted({r["modality"] for r in selected}),
        "downloaded_count": 0,
        "verified_count": 0,
        "files": selected,
    }


def write_acquisition_manifest(output: str | Path, manifest: dict) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_tsv_manifest(output: str | Path, manifest: dict) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "file_id", "file_name", "file_size", "md5sum", "access",
        "data_category", "data_type", "data_format", "experimental_strategy",
        "modality", "download_status", "local_path", "verified",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", delimiter="\t")
        writer.writeheader()
        writer.writerows(manifest.get("files", []))
    return path


def md5_file(path: str | Path) -> str:
    digest = hashlib.md5()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: str | Path, expected_md5: str | None, expected_size: int | None = None) -> dict:
    path = Path(path)
    if not path.exists():
        return {"status": "Data unavailable", "verified": False, "reason": "local_file_missing"}
    actual_size = path.stat().st_size
    size_ok = expected_size is None or actual_size == int(expected_size)
    actual_md5 = md5_file(path)
    md5_ok = expected_md5 is None or actual_md5.lower() == str(expected_md5).lower()
    return {
        "status": "PASS" if size_ok and md5_ok else "FAIL",
        "verified": bool(size_ok and md5_ok),
        "actual_size": actual_size,
        "expected_size": expected_size,
        "actual_md5": actual_md5,
        "expected_md5": expected_md5,
        "size_ok": size_ok,
        "md5_ok": md5_ok,
    }


def _download_with_curl(url: str, target: Path, headers: dict[str, str], timeout: int) -> None:
    """Fallback downloader for environments where urllib hits TLS EOF resets."""
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl executable is not available")
    command = [
        curl, "--fail", "--location", "--retry", "3", "--retry-delay", "2",
        "--retry-all-errors", "--connect-timeout", str(max(10, min(int(timeout), 60))),
        "--output", str(target),
    ]
    for key, value in headers.items():
        command.extend(["--header", f"{key}: {value}"])
    command.append(url)
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"curl exited with code {completed.returncode}")


def download_file(file_row: dict, output_dir: str | Path, token: str | None = None,
                  timeout: int = 60, overwrite: bool = False) -> dict:
    file_id = str(file_row.get("file_id") or "").strip()
    if not file_id:
        raise ValueError("file_id is required")
    if str(file_row.get("access", "")).lower() == "controlled" and not token:
        token = os.environ.get("GDC_TOKEN")
    if str(file_row.get("access", "")).lower() == "controlled" and not token:
        return {"status": "Data unavailable", "verified": False, "reason": "gdc_token_required"}
    name = Path(str(file_row.get("file_name") or file_id)).name
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    target = root / name
    if target.exists() and not overwrite:
        verification = verify_file(target, file_row.get("md5sum"), file_row.get("file_size"))
        return {"status": "EXISTS", "path": str(target), **verification}
    headers = {"User-Agent": "WGR-CDP/1.2"}
    if token:
        headers["X-Auth-Token"] = token
    request = Request(f"{GDC_API}/data/{file_id}", headers=headers)
    temp = target.with_suffix(target.suffix + ".part")
    try:
        with urlopen(request, timeout=timeout) as response, temp.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        temp.replace(target)
    except Exception as exc:
        if temp.exists():
            temp.unlink()
        try:
            _download_with_curl(request.full_url, temp, headers, timeout)
            temp.replace(target)
        except Exception as fallback_exc:
            if temp.exists():
                temp.unlink()
            raise GDCIntakeError(
                f"GDC download failed: {type(exc).__name__}; curl fallback: {type(fallback_exc).__name__}"
            ) from fallback_exc
    verification = verify_file(target, file_row.get("md5sum"), file_row.get("file_size"))
    if not verification["verified"] and target.exists():
        target.unlink()
    return {"status": "PASS" if verification["verified"] else "FAIL",
            "path": str(target), **verification}


def acquire_manifest(manifest: dict, output_dir: str | Path, *,
                     token: str | None = None, limit: int | None = None) -> dict:
    files = manifest.get("files") or []
    if limit is not None:
        files = files[:limit]
    results = []
    for row in files:
        result = download_file(row, output_dir, token=token)
        row["download_status"] = result["status"]
        row["local_path"] = result.get("path")
        row["verified"] = result.get("verified", False)
        row["verification"] = result
        results.append(result)
    expected_size_bytes = sum(int(row.get("file_size") or 0) for row in files)
    downloaded_size_bytes = sum(
        int(r.get("actual_size") or 0)
        for r in results
        if r.get("verified")
    )
    manifest["selected_size_bytes"] = expected_size_bytes
    manifest["selected_size_mb"] = round(expected_size_bytes / 1024**2, 2)
    manifest["selected_size_gb"] = round(expected_size_bytes / 1024**3, 3)
    manifest["downloaded_size_bytes"] = downloaded_size_bytes
    manifest["downloaded_size_mb"] = round(downloaded_size_bytes / 1024**2, 2)
    manifest["downloaded_size_gb"] = round(downloaded_size_bytes / 1024**3, 3)
    manifest["downloaded_count"] = sum(r.get("status") in {"PASS", "EXISTS"} for r in results)
    manifest["verified_count"] = sum(bool(r.get("verified")) for r in results)
    if not results:
        manifest["acquisition_status"] = "Data unavailable"
    elif manifest["verified_count"] == len(results):
        manifest["acquisition_status"] = "PASS"
    elif manifest["verified_count"] == 0 and all(
        r.get("status") == "Data unavailable" for r in results
    ):
        manifest["acquisition_status"] = "Data unavailable"
    else:
        manifest["acquisition_status"] = "CONDITIONAL"
    return manifest


def register_dataset(manifest: dict, root: str | Path) -> dict:
    root = Path(root)
    registered = []
    for row in manifest.get("files", []):
        if not row.get("verified"):
            continue
        path = Path(row.get("local_path") or "")
        if not path.is_absolute():
            path = root / path
        registered.append({
            "file_id": row.get("file_id"),
            "file_name": row.get("file_name"),
            "local_path": str(path),
            "md5sum": row.get("md5sum"),
            "file_size": row.get("file_size"),
            "modality": row.get("modality", classify_file(row)),
            "access": row.get("access"),
            "genome_build": "Data unavailable",
            "sample_ids": "Data unavailable",
            "validated_for_analysis": False,
        })
    return {
        "schema_version": "A11-REG-1",
        "status": "Available" if registered else "Data unavailable",
        "project_id": manifest.get("project_id", "Data unavailable"),
        "registered_count": len(registered),
        "analysis_ready_count": 0,
        "files": registered,
        "reason": "genome_build_and_sample_manifest_validation_required",
    }


def write_registration(output: str | Path, registration: dict) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registration, indent=2, sort_keys=True), encoding="utf-8")
    return path
