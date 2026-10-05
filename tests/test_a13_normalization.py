from pathlib import Path

from wgr_cdp.data_ingestion.normalize import normalize_variant, normalize_vcf, read_fasta


def test_left_align_insertion_through_repeat():
    reference = {"chr1": "CAAAA"}
    result = normalize_variant(
        {"chrom": "1", "pos": 4, "ref": "A", "alt": "AA"},
        reference=reference,
    )
    assert result["chrom"] == "1"
    assert result["pos"] == 2
    assert result["ref"] == "A"
    assert result["alt"] == "AA"
    assert result["reference_validation"] == "match"
    assert result["normalization_status"] == "reference_aware"


def test_left_align_deletion_through_repeat():
    reference = {"chr1": "CAAAA"}
    result = normalize_variant(
        {"chrom": "1", "pos": 4, "ref": "AA", "alt": "A"},
        reference=reference,
    )
    assert result["pos"] == 2
    assert result["ref"] == "AA"
    assert result["alt"] == "A"


def test_reference_mismatch_is_not_claimed_normalized():
    reference = {"1": "ACGT"}
    result = normalize_variant(
        {"chrom": "1", "pos": 2, "ref": "T", "alt": "A"},
        reference=reference,
    )
    assert result["normalization_status"] == "reference_mismatch"
    assert result["reference_validation"] == "mismatch"


def test_normalize_vcf_expands_multiallelic_and_deduplicates(tmp_path):
    fasta = tmp_path / "ref.fa"
    fasta.write_text(">chr1\nCAAAA\n", encoding="utf-8")
    source = tmp_path / "input.vcf"
    source.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        "1\t4\t.\tA\tAA,AA\t.\tPASS\tSOURCE=TEST\n",
        encoding="utf-8",
    )
    output = tmp_path / "normalized.vcf"

    result = normalize_vcf(source, output, fasta, reference_build="GRCh38")

    assert result["status"] == "PASS"
    assert result["input_record_count"] == 1
    assert result["expanded_record_count"] == 2
    assert result["deduplicated_record_count"] == 1
    text = output.read_text(encoding="utf-8")
    assert "##reference=GRCh38" in text
    assert "##wgr_cdp_normalization_status=reference_aware" in text
    assert "\t2\t.\tA\tAA\t" in text
    assert "WGR_NORM=reference_aware" in text


def test_read_fasta_rejects_sequence_before_header(tmp_path):
    fasta = tmp_path / "bad.fa"
    fasta.write_text("ACGT\n", encoding="utf-8")
    try:
        read_fasta(fasta)
    except ValueError as exc:
        assert "before a header" in str(exc)
    else:
        raise AssertionError("Expected FASTA header validation failure")
