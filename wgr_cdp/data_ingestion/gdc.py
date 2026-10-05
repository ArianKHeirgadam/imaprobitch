"""GDC/TCGA dataset intake and provenance utilities for WGR-CDP.

This layer discovers released GDC project metadata and open/controlled file
inventory metadata without downloading biological data or inventing cohort
counts. It is an intake/provenance layer; downstream analysis consumes local
files only after explicit acquisition.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GDC_API = "https://api.gdc.cancer.gov"


class GDCIntakeError(RuntimeError):
    """Raised when GDC intake cannot retrieve or validate metadata."""


def _get_json(url: str, timeout: int = 20) -> dict:
    last_exc = None
    for attempt in range(3):
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Connection": "close",
                "User-Agent": "WGR-CDP/1.4",
            },
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(1.0 * (attempt + 1))
    raise GDCIntakeError(
        f"GDC request failed after 3 attempts: {type(last_exc).__name__}"
    ) from last_exc


def fetch_project(project_id: str, timeout: int = 20) -> dict:
    project_id = str(project_id).strip()
    if not project_id:
        raise ValueError("project_id is required")
    fields = ",".join([
        "project_id", "name", "program.name", "disease_type",
        "primary_site", "released", "state", "dbgap_accession_number",
        "summary.case_count", "summary.file_count", "summary.file_size",
    ])
    query = urlencode({"fields": fields, "expand": "summary", "pretty": "false"})
    payload = _get_json(f"{GDC_API}/projects/{project_id}?{query}", timeout=timeout)
    data = payload.get("data")
    if not isinstance(data, dict):
        raise GDCIntakeError("GDC project response did not contain data")
    return data


def query_files(project_id: str, *, data_category: str | None = None,
                access: str | None = None, size: int = 100,
                timeout: int = 20) -> dict:
    if size < 1 or size > 5000:
        raise ValueError("size must be between 1 and 5000")
    content = [{
        "op": "in",
        "content": {"field": "cases.project.project_id", "value": [project_id]},
    }]
    if data_category:
        content.append({
            "op": "in",
            "content": {"field": "data_category", "value": [data_category]},
        })
    if access:
        content.append({
            "op": "in",
            "content": {"field": "access", "value": [access]},
        })
    filters = json.dumps({"op": "and", "content": content}, separators=(",", ":"))
    fields = ",".join([
        "file_id", "file_name", "file_size", "md5sum", "data_category",
        "data_format", "access", "experimental_strategy",
        "cases.project.project_id",
    ])
    query = urlencode({
        "filters": filters, "fields": fields, "format": "JSON", "size": str(size),
    })
    return _get_json(f"{GDC_API}/files?{query}", timeout=timeout)


def build_intake_record(project: dict, file_payload: dict | None = None) -> dict:
    summary = project.get("summary") if isinstance(project.get("summary"), dict) else {}
    hits = []
    if isinstance(file_payload, dict):
        data = file_payload.get("data") or {}
        hits = data.get("hits") if isinstance(data.get("hits"), list) else []
    return {
        "schema_version": "A10-1",
        "status": "Available",
        "source": "GDC",
        "project_id": project.get("project_id", "Data unavailable"),
        "project_name": project.get("name", "Data unavailable"),
        "program": project.get("program", {}).get("name", "Data unavailable")
            if isinstance(project.get("program"), dict) else "Data unavailable",
        "disease_type": project.get("disease_type", "Data unavailable"),
        "primary_site": project.get("primary_site", "Data unavailable"),
        "released": project.get("released", "Data unavailable"),
        "state": project.get("state", "Data unavailable"),
        "dbgap_accession_number": project.get("dbgap_accession_number", "Data unavailable"),
        "summary": {
            "case_count": summary.get("case_count", "Data unavailable"),
            "file_count": summary.get("file_count", "Data unavailable"),
            "file_size": summary.get("file_size", "Data unavailable"),
        },
        "files": hits,
        "downloaded_locally": False,
        "clinical_or_biological_results": "Data unavailable",
    }


def write_intake_record(output: str | Path, record: dict) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return path
