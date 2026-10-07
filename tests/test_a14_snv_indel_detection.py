from wgr_cdp.research.snv_indel_detection import (
    classify_variant, parse_vcf, detect_snv_indel, write_detection_artifacts,
)


def _vcf(path, sample, records):
    path.write_text(
        "##fileformat=VCFv4.2\n"
        "##reference=GRCh38\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
        + sample + "\n"
        + "".join(records),
        encoding="utf-8",
    )


def test_classify_snv_indel():
    assert classify_variant("A", "G") == "SNV"
    assert classify_variant("A", "AT") == "INDEL"
    assert classify_variant("AT", "A") == "INDEL"
    assert classify_variant("AT", "GC") is None
    assert classify_variant("A", "<DEL>") is None


def test_parse_vcf_extracts_vaf_depth_and_multiallelic(tmp_path):
    path = tmp_path / "c.vcf"
    _vcf(path, "C1", [
        "1\t100\t.\tA\tG,AT\t60\tPASS\tGENE=TP53\tGT:DP:AD\t1/2:100:10,40,50\n"
    ])
    rows = parse_vcf(path, group="cancer")
    assert [r["feature_type"] for r in rows] == ["SNV", "INDEL"]
    assert rows[0]["vaf"] == .4
    assert rows[0]["depth"] == 100
    assert rows[0]["gene"] == "TP53"


def test_filter_is_strict_and_missing_is_not_negative(tmp_path):
    path = tmp_path / "h.vcf"
    _vcf(path, "H1", [
        "1\t100\t.\tA\tG\t60\tPASS\t.\tGT:DP:AD\t0/1:10:5,5\n",
        "1\t200\t.\tC\tT\t60\tPASS\t.\tGT:DP:AD\t./.:.:.\n",
        "1\t300\t.\tG\tA\t60\tLowQual\t.\tGT:DP:AD\t1/1:10:0,10\n",
    ])
    rows = parse_vcf(path, group="healthy")
    assert len(rows) == 2
    assert rows[0]["status"] == "Detected"
    assert rows[1]["status"] == "Data unavailable"
    assert all(row["pos"] != 300 for row in rows)
def test_cohort_detection_and_fdr(tmp_path):
    cancer = tmp_path / "c.vcf"
    healthy = tmp_path / "h.vcf"
    _vcf(cancer, "C1", [
        "1\t100\t.\tA\tG\t60\tPASS\t.\tGT:DP:AD\t1/1:100:0,100\n",
        "1\t200\t.\tA\tAT\t60\tPASS\t.\tGT:DP:AD\t1/1:100:0,100\n",
    ])
    _vcf(healthy, "H1", [
        "1\t100\t.\tA\tG\t60\tPASS\t.\tGT:DP:AD\t0/0:100:100,0\n",
        "1\t200\t.\tA\tAT\t60\tPASS\t.\tGT:DP:AD\t0/0:100:100,0\n",
    ])
    result = detect_snv_indel([cancer], [healthy])
    assert result["status"] == "PASS"
    assert {r["feature_type"] for r in result["results"]} == {"SNV", "INDEL"}
    assert all("q_value" in r for r in result["results"])


def test_no_observation_is_not_negative(tmp_path):
    cancer = tmp_path / "c.vcf"
    healthy = tmp_path / "h.vcf"
    _vcf(cancer, "C1", ["1\t100\t.\tA\tG\t60\tPASS\t.\tGT\t1/1\n"])
    _vcf(healthy, "H1", ["1\t200\t.\tC\tT\t60\tPASS\t.\tGT\t1/1\n"])
    result = detect_snv_indel([cancer], [healthy])
    assert result["status"] == "PASS"
    assert result["results"][0]["control_frequency"] is None


def test_artifacts(tmp_path):
    path = tmp_path / "c.vcf"
    _vcf(path, "C1", ["1\t100\t.\tA\tG\t60\tPASS\t.\tGT\t1/1\n"])
    result = detect_snv_indel([path], [path])
    out = tmp_path / "out"
    write_detection_artifacts(result, out)
    assert (out / "snv_indel_observations.csv").exists()
    assert (out / "snv_indel_detection.csv").exists()


def test_real_cancer_side_validation_is_explicitly_conditional_without_control(tmp_path):
    cancer = tmp_path / "cancer.vcf"
    _vcf(cancer, "C1", [
        "1\t100\t.\tA\tG\t60\tPASS\tGENE=TP53\tGT:DP:AD\t1/1:100:0,100\n",
        "2\t200\t.\tA\tAT\t60\tPASS\t.\tGT:DP:AD\t1/1:100:0,100\n",
    ])
    from wgr_cdp.research.snv_indel_detection import validate_snv_indel_cohort
    result = validate_snv_indel_cohort([cancer])
    assert result["status"] == "PASS"
    assert result["control_status"] == "Data unavailable"
    assert result["observation_count"] == 2
    assert result["snv_count"] == 1
    assert result["indel_count"] == 1
