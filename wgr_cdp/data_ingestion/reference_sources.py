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
    + "20201028_CCDG_14151_B01_GRM_WGS_2020-08-05_chr{chrom}."
    + "recalibrated_variants.vcf.gz"
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
    "tcga_matched_normal": SourceProfile(
        "TCGA-STAD matched normal", "Paired non-tumor comparator", "controlled",
        "Data unavailable until file inspection", "germline/somatic-normal VCF",
        "https://portal.gdc.cancer.gov/projects/TCGA-STAD",
        "Matched non-tumor samples belong to the same cancer cases. They are useful "
        "for paired somatic-vs-normal analyses but are not an independent healthy "
        "population and should not be described as such.",
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
        "paired_normal_reference": asdict(profiles["tcga_matched_normal"]),
        "tissue_reference": asdict(profiles["gtex_stomach"]) if include_gtex else None,
        "healthy_target_samples": int(healthy_target_samples),
        "chromosomes": list(chromosomes),
        "analysis_roles": {
            "Cancer": "TCGA-STAD discovery candidates",
            "Healthy/reference": (
                "1000 Genomes population/germline reference; not automatically "
                "declared disease-matched healthy control"
            ),
            "TCGA matched normal": (
                "paired non-tumor comparator for the same cancer cases; not an "
                "independent healthy population"
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

def read_1000g_panel(path: str | Path) -> list[dict]:
    import csv
    path = Path(path)
    if not path.exists():
        raise ValueError(f"1000 Genomes sample panel does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        return []
    required = {"sample", "population", "super_population"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError("1000 Genomes panel missing columns: " + ", ".join(sorted(missing)))
    return rows

def select_1000g_samples(panel_rows, n=250, strategy="balanced_superpopulation"):
    if n < 1:
        raise ValueError("n must be positive")
    rows = [dict(r) for r in panel_rows if r.get("sample")]
    if n >= len(rows):
        return rows
    if strategy != "balanced_superpopulation":
        return rows[:n]
    groups = {}
    for row in rows:
        groups.setdefault(str(row.get("super_population") or UNAVAILABLE), []).append(row)
    labels = sorted(groups)
    quota, remainder = divmod(n, len(labels))
    selected = []
    for index, label in enumerate(labels):
        take = quota + (1 if index < remainder else 0)
        selected.extend(groups[label][:take])
    return selected[:n]

def write_sample_list(path: str | Path, rows: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(str(row["sample"]) for row in rows if row.get("sample")) + "\n",
        encoding="utf-8",
    )
    return path

def subset_vcf_samples(input_path: str | Path, output_path: str | Path, sample_ids):
    import gzip
    input_path = Path(input_path)
    output_path = Path(output_path)
    wanted = set(str(x) for x in sample_ids)
    if not wanted:
        raise ValueError("sample_ids cannot be empty")
    opener_in = gzip.open if input_path.suffix == ".gz" else open
    opener_out = gzip.open if output_path.suffix == ".gz" else open
    output_path.parent.mkdir(parents=True, exist_ok=True)
    found = set()
    with opener_in(input_path, "rt", encoding="utf-8") as src, opener_out(output_path, "wt", encoding="utf-8") as dst:
        for raw in src:
            if raw.startswith("##"):
                dst.write(raw)
                continue
            if raw.startswith("#CHROM"):
                fields = raw.rstrip("\r\n").split("\t")
                base = fields[:9]
                sample_names = fields[9:]
                indices = [i for i, name in enumerate(sample_names, start=9) if name in wanted]
                found = {sample_names[i - 9] for i in indices}
                dst.write("\t".join(base + [fields[i] for i in indices]) + "\n")
                continue
            fields = raw.rstrip("\r\n").split("\t")
            if len(fields) >= 9:
                format_and_samples = [fields[i] for i in indices]
                dst.write("\t".join(fields[:9] + format_and_samples) + "\n")
            else:
                dst.write(raw)
    missing = sorted(wanted - found)
    if missing:
        raise ValueError("requested sample IDs not found in VCF: " + ", ".join(missing[:10]))
    return {"status": "Available", "selected_sample_count": len(found), "output": str(output_path)}

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
