from wgr_cdp.application.analysis import analyze_cohorts


def _write_vcf(path, records):
    lines = ["##fileformat=VCFv4.2", "#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO"]
    for row in records:
        lines.append("\\t".join(map(str, row)))
    path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")


def test_real_end_to_end_analysis(tmp_path):
    healthy = tmp_path / "healthy"
    cancer = tmp_path / "cancer"
    output = tmp_path / "results"
    healthy.mkdir()
    cancer.mkdir()
    _write_vcf(healthy / "H1.vcf", [("17", 100, ".", "A", "G", ".", "PASS", "GENE=TP53")])
    _write_vcf(healthy / "H2.vcf", [])
    _write_vcf(cancer / "C1.vcf", [("17", 100, ".", "A", "G", ".", "PASS", "GENE=TP53"), ("1", 200, ".", "C", "T", ".", "PASS", "GENE=GENE2")])
    _write_vcf(cancer / "C2.vcf", [("17", 100, ".", "A", "G", ".", "PASS", "GENE=TP53")])
    result = analyze_cohorts(healthy, cancer, output)
    assert result["summary"]["control_samples"] == 2
    assert result["summary"]["case_samples"] == 2
    assert result["summary"]["unique_variants"] == 2
    assert (output / "candidates.csv").exists()
    assert (output / "report.html").exists()


def test_missing_input_is_rejected(tmp_path):
    try:
        analyze_cohorts(tmp_path / "missing", tmp_path / "cancer", tmp_path / "out")
    except ValueError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("missing input directory should fail")
