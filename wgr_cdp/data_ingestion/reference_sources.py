"""Real-data source profiles and deterministic acquisition planning.

The planner distinguishes a primary Cancer cohort from population/tissue
reference cohorts. It never labels GTEx or 1000 Genomes as disease-matched
healthy controls without an explicit study decision.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from urllib.request import Request, urlopen

UNAVAILABLE = "Data unavailable"

ONE_KG_30X_BASE = (
    "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/"
    "1000G_2504_high_coverage/working/"
    "20201028_3202_raw_GT_with_annot/"
)
ONE_KG_30X_VARIANT_TEMPLATE = (
    ONE_KG_30X_BASE
    "20201028_CCDG_14151_B01_GRM_WGS_2020-08-05_chr{chrom}."
    "recalibrated_variants.vcf.gz"
)
ONE_KG_SAMPLE_PANEL = (
    "https://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20130502/"
    "integrated_call_samples_v3.20130502.ALL.panel"
)
GTEX_PORTAL = "https://gtexportal.org/home/downloads/adult-gtex/"
GDC_PROJECT = "TCGA-STAD"

@dataclass(frozen=True)
class SourceProfile:
    name: str
    role: str
    access: str
    genome_build: str
    format: str
    source_url: str
    notes: str

SOURCE_PROFILES = {
    "tcga_stad": SourceProfile(
        "TCGA-STAD", "Cancer discovery cohort", "GDC open + controlled",
        "Data unavailable until file inspection", "MAF / VCF / CNV",
        "https://portal.gdc.cancer.gov/projects/TCGA-STAD",
        "Prefer harmonized WGS somatic VCF when access and file-level metadata "
        "permit; open masked somatic MAF is an explicit fallback and must remain "
        "labelled as MAF-derived rather than raw WGS VCF.",
    ),
    "1000g_30x": SourceProfile(
        "1000 Genomes 30x", "Population/germline reference cohort", "public",
        "GRCh38", "multi-sample VCF.gz",
        "https://www.internationalgenome.org/data-portal/data-collection/1000genomes_30x",
        "2504 unrelated phase-3 panel is the preferred public high-coverage "
        "reference set; use only after population/case-control harmonization review "
        "if treated as a formal healthy comparator.",
    ),
    "gtex_stomach": SourceProfile(
        "GTEx Stomach", "Non-diseased tissue reference", "open + protected",
        "Data unavailable", "GTEx open datasets / protected WGS",
        GTEX_PORTAL,
        "GTEx provides non-diseased tissue references. Raw sequence and full donor "
        "metadata are protected, so this source is not silently treated as an open "
        "healthy WGS VCF cohort.",
    ),
}

def build_data_plan(
    *,
    cancer_project: str = GDC_PROJECT,
    healthy_reference: str = "1000g_30x",
    include_gtex: bool = True,
    healthy_target_samples: int = 250,
    chromosomes: tuple[str, ...] = tuple(str(i) for i in range(1, 23)) + ("X",),
):
    if healthy_target_samples < 1:
        raise ValueError("healthy_target_samples must be positive")
    profiles = dict(SOURCE_PROFILES)
    profiles["tcga_stad"] = SourceProfile(
        **{**asdict(profiles["tcga_stad"]), "name": cancer_project,
         "source_url": f"https://portal.gdc.cancer.gov/projects/{cancer_project}"}
    )
    plan = {
        "schema_version": "A12-DATA-1",
        "status": "Available",
        "primary_cancer": asdict(profiles["tcga_stad"]),
        "healthy_reference": asdict(profiles[healthy_reference]),
        "tissue_reference": asdict(profiles["gtex_stomach"]) if include_gtex else None,
        "healthy_target_samples": int(healthy_target_samples),
        "chromosomes": list(chromosomes),
        "analysis_roles": {
            "Cancer": "TCGA-STAD discovery candidates",
            "Healthy/reference": (
                "1000 Genomes population/germline reference; not automatically "
                "declared disease-matched healthy control"
            ),
            "GTEx": "non-diseased stomach tissue reference",
        },
        "scientific_gate": (
            "A case-control claim requires compatible sample type, genome build, "
            "variant semantics, population background and technical metadata."
        ),
    }
    return plan

def write_data_plan(path: str | Path, plan: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    return path

def one_kg_urls(chromosomes=None):
    chromosomes = chromosomes or tuple(str(i) for i in range(1, 23)) + ("X",)
    return [{
        "chromosome": str(chrom),
        "url": ONE_KG_30X_VARIANT_TEMPLATE.format(chrom=chrom),
        "index_url": ONE_KG_30X_VARIANT_TEMPLATE.format(chrom=chrom) + ".tbi",
        "format": "VCF.gz",
        "genome_build": "GRCh38",
        "access": "public",
        "source": "1000 Genomes 30x",
    } for chrom in chromosomes]

def download_url(url: str, path: str | Path, *, timeout: int = 60, overwrite: bool = False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return {"status": "EXISTS", "path": str(path)}
    request = Request(url, headers={"User-Agent": "WGR-CDP/1.4"})
    temp = path.with_suffix(path.suffix + ".part")
    try:
        with urlopen(request, timeout=timeout) as response, temp.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        temp.replace(path)
    except Exception as exc:
        if temp.exists():
            temp.unlink()
        return {"status": "FAIL", "path": str(path), "reason": type(exc).__name__}
    return {"status": "PASS", "path": str(path)}
