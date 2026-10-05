from wgr_cdp.data_ingestion.maf import read_maf


def test_read_maf_detects_header_after_metadata(tmp_path):
    path = tmp_path / "sample.maf"
    path.write_text(
        "#version 2.4\n"
        "##fileformat=MAF\n"
        "metadata\tvalue\n"
        "Hugo_Symbol\tChromosome\tStart_Position\tReference_Allele\t"
        "Tumor_Seq_Allele2\tTumor_Sample_Barcode\n"
        "TP53\t17\t7579472\tC\tT\tTCGA-TEST-01A\n",
        encoding="utf-8",
    )
    rows = read_maf(path)
    assert len(rows) == 1
    assert rows[0]["Chromosome"] == "17"
    assert rows[0]["Tumor_Sample_Barcode"] == "TCGA-TEST-01A"
