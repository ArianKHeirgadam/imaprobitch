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



def test_reference_aware_indel_conversion_uses_vcf_anchor(tmp_path):
    source_dir = tmp_path / "maf"
    out_dir = tmp_path / "vcf"
    source_dir.mkdir()
    source = source_dir / "indel.maf"
    source.write_text(
        "Hugo_Symbol\tChromosome\tStart_Position\tEnd_Position\t"
        "Reference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\t"
        "Variant_Classification\tVariant_Type\n"
        "ZC3H15\t2\t5\t5\t-\tGA\tTCGA-TEST-01A\t"
        "Frame_Shift_Ins\tINS\n"
        "ZC3H15\t2\t10\t11\tAC\t-\tTCGA-TEST-01A\t"
        "Frame_Shift_Del\tDEL\n",
        encoding="utf-8",
    )
    fasta = tmp_path / "ref.fa"
    fasta.write_text(">chr2\nTTTTGCCCCACCC\n", encoding="utf-8")

    result = convert_maf_directory_to_vcf(
        source_dir, out_dir, pattern="*.maf", reference=fasta
    )

    assert result["status"] == "PASS"
    vcf = next(out_dir.glob("*.vcf"))
    lines = [
        line.split("\t")
        for line in vcf.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]
    assert any(row[1:5] == ["5", ".", "G", "GGA"] for row in lines)
    assert any(row[1:5] == ["9", ".", "CAC", "C"] for row in lines)
    assert all(row[3] != "-" and row[4] != "-" for row in lines)
