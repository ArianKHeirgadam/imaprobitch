"""A9 reproducibility and release-manifest utilities."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_artifact_manifest(output_dir, exclude_names=()):
    """Hash output artifacts for exact post-run provenance."""
    root = Path(output_dir)
    excluded = set(exclude_names)
    if not root.exists():
        return {"status": "Data unavailable", "reason": "output_directory_missing"}
    artifacts = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel in excluded:
            continue
        artifacts.append({
            "path": rel,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {"status": "Available", "artifact_count": len(artifacts), "artifacts": artifacts}


def build_reproducibility_manifest(
    output_dir,
    config=None,
    release_metadata=None,
    run_id=None,
):
    """Create a deterministic environment/config/artifact provenance record."""
    from .metadata import RELEASE_METADATA

    metadata = dict(release_metadata or RELEASE_METADATA)
    return {
        "schema_version": "A9-1",
        "status": "Available",
        "run_id": run_id or "Data unavailable",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "release": metadata.get("release", "Data unavailable"),
        "project": metadata.get("name", "Data unavailable"),
        "python": sys.version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "config": dict(config or {}),
        "scientific_scope": metadata.get("scope", "Data unavailable"),
        "clinical_diagnostic": metadata.get("clinical_diagnostic", "Data unavailable"),
        "artifacts": collect_artifact_manifest(
            output_dir,
            exclude_names={"reproducibility_manifest.json"},
        ),
    }


def write_reproducibility_manifest(output_dir, config=None, release_metadata=None, run_id=None):
    """Write the A9 machine-readable manifest into the run directory."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    manifest = build_reproducibility_manifest(
        root, config=config, release_metadata=release_metadata, run_id=run_id
    )
    path = root / "reproducibility_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return path


def release_readiness():
    """Return release readiness without making biological claims."""
    from .health import run_health_check

    health = run_health_check()
    return {
        "status": "PASS" if health["passed"] else "FAIL",
        "health": health,
        "reproducibility_manifest_supported": True,
        "scientific_results": "CONDITIONAL",
        "reason": "real-data empirical validation remains data-dependent",
    }
