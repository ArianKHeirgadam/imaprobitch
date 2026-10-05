from pathlib import Path

from wgr_cdp.data_ingestion.maf import convert_maf_to_vcf, read_maf


def test_read_maf(tmp_path):
    path = tmp_path / "x.maf"
    path.write_text(
        "Hugo_Symbol\tChromosome\tStart_Position\tEnd_Position\t"
        "Reference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\t"
        "Variant_Type\tVariant_Classification\n"
        "TP53\t17\t100\t100\tC\tT\tTCGA-01-0001-01\tSNP\tMissense_Mutation\n",
        encoding="utf-8",
    )
    rows = read_maf(path)
    assert rows[0]["Tumor_Sample_Barcode"] == "TCGA-01-0001-01"


def test_maf_to_per_sample_vcf_preserves_provenance(tmp_path):
    maf = tmp_path / "x.maf"
    maf.write_text(
        "Hugo_Symbol\tChromosome\tStart_Position\tEnd_Position\t"
        "Reference_Allele\tTumor_Seq_Allele2\tTumor_Sample_Barcode\t"
        "Variant_Type\tVariant_Classification\n"
        "TP53\t17\t100\t100\tC\tT\tTCGA-01-0001-01\tSNP\tMissense_Mutation\n"
        "KRAS\t12\t200\t200\tG\tA\tTCGA-01-0001-02\tSNP\tMissense_Mutation\n",
        encoding="utf-8",
    )
    result = convert_maf_to_vcf(maf, tmp_path / "out")
    assert result["sample_count"] == 2
    assert result["normalization_required"] is True
    vcf = Path(result["files"][0]["path"])
    text = vcf.read_text(encoding="utf-8")
    assert "SOURCE=GDC_MASKED_SOMATIC_MAF" in text
    assert "#CHROM\tPOS" in text
