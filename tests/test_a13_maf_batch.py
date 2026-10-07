from pathlib import Path

from wgr_cdp.data_ingestion.maf import convert_maf_directory_to_vcf


def test_convert_maf_directory_to_vcf_and_qc(tmp_path):
    source_dir = tmp_path / "maf"
    out_dir = tmp_path / "vcf"
    source_dir.mkdir()
    source = source_dir / "sample.maf"
    source.write_text(
        "Hugo_Symbol\tChromosome\tStart_Position\tReference_Allele\t"
        "Tumor_Seq_Allele2\tTumor_Sample_Barcode\tVariant_Classification\n"
        "TP53\t17\t7579472\tC\tT\tTCGA-TEST-01A\tMissense_Mutation\n",
        encoding="utf-8",
    )

    result = convert_maf_directory_to_vcf(
        source_dir, out_dir, pattern="*.maf"
    )

    assert result["status"] == "PASS"
    assert result["input_file_count"] == 1
    assert result["converted_file_count"] == 1
    assert result["variant_record_count"] == 1
    assert result["qc_invalid_record_count"] == 0
    assert result["qc_missing_source_tag_count"] == 0

    vcfs = list(out_dir.glob("*.vcf"))
    assert len(vcfs) == 1
    assert "SOURCE=GDC_MASKED_SOMATIC_MAF" in vcfs[0].read_text(encoding="utf-8")


def test_valid_header_with_zero_variant_rows_is_available_not_unavailable(tmp_path):
    source_dir = tmp_path / "maf"
    out_dir = tmp_path / "vcf"
    source_dir.mkdir()
    source = source_dir / "empty.maf"
    source.write_text(
        "Hugo_Symbol\tChromosome\tStart_Position\tReference_Allele\t"
        "Tumor_Seq_Allele2\tTumor_Sample_Barcode\tVariant_Classification\n",
        encoding="utf-8",
    )

    result = convert_maf_directory_to_vcf(source_dir, out_dir, pattern="*.maf")

    item = result["results"][0]["conversion"]
    assert item["status"] == "Available"
    assert item["empty_source"] is True
    assert item["sample_count"] == 0
    assert item["record_count"] == 0
    assert result["empty_source_count"] == 1
    assert result["status"] == "CONDITIONAL"
