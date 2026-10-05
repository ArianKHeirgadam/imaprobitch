from pathlib import Path
import gzip

from wgr_cdp.data_ingestion import reference_sources as r


def test_data_plan_roles_are_explicit():
    plan = r.build_data_plan(healthy_target_samples=250)
    assert plan["schema_version"] == "A12-DATA-1"
    assert plan["primary_cancer"]["role"] == "Cancer discovery cohort"
    assert plan["healthy_reference"]["role"] == "Population/germline reference cohort"
    assert plan["tissue_reference"]["role"] == "Non-diseased tissue reference"


def test_1000g_urls_are_grch38_public():
    urls = r.one_kg_urls(("1", "X"))
    assert len(urls) == 2
    assert all(item["genome_build"] == "GRCh38" for item in urls)
    assert urls[0]["url"].endswith("chr1.recalibrated_variants.vcf.gz")


def test_1000g_selection_balances_superpopulations():
    rows = []
    for label in ("AFR", "AMR", "EAS", "EUR", "SAS"):
        for i in range(10):
            rows.append({"sample": f"{label}{i}", "population": label, "super_population": label})
    selected = r.select_1000g_samples(rows, 10)
    counts = {label: sum(x["super_population"] == label for x in selected) for label in ("AFR","AMR","EAS","EUR","SAS")}
    assert counts == {"AFR": 2, "AMR": 2, "EAS": 2, "EUR": 2, "SAS": 2}


def test_read_panel_and_write_sample_list(tmp_path):
    panel = tmp_path / "panel.txt"
    panel.write_text(
        "sample\tpopulation\tsuper_population\tgender\n"
        "A\tPOP1\tEUR\tF\nB\tPOP2\tAFR\tM\n",
        encoding="utf-8",
    )
    rows = r.read_1000g_panel(panel)
    assert len(rows) == 2
    out = r.write_sample_list(tmp_path / "samples.txt", rows)
    assert out.read_text(encoding="utf-8").splitlines() == ["A", "B"]


def test_subset_vcf_samples(tmp_path):
    source = tmp_path / "all.vcf"
    source.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\tC\n"
        "1\t10\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/0\t1/1\n",
        encoding="utf-8",
    )
    out = tmp_path / "subset.vcf.gz"
    result = r.subset_vcf_samples(source, out, ["A", "C"])
    assert result["selected_sample_count"] == 2
    with gzip.open(out, "rt", encoding="utf-8") as handle:
        text = handle.read()
    assert "#CHROM\tPOS" in text
    assert text.splitlines()[1].endswith("\tA\tC")


def test_download_url_exists_without_network(tmp_path):
    path = tmp_path / "existing.bin"
    path.write_bytes(b"x")
    result = r.download_url("https://example.invalid/file", path)
    assert result["status"] == "EXISTS"
