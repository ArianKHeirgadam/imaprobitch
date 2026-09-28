from wgr_cdp.data_ingestion.vcf_cohort import read_vcf_cohort


def test_multiallelic_is_decomposed(tmp_path):
    path = tmp_path / "cohort.vcf"
    path.write_text("##fileformat=VCFv4.2\\n#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO\\n1\\t100\\t.\\tA\\tC,G\\t.\\tPASS\\tGENE=X\\n", encoding="utf-8")
    samples = read_vcf_cohort(path, "case")
    assert len(samples) == 1
    assert samples[0]["variants"] == ["1:100:A:C", "1:100:A:G"]
    assert all(r["variant_type"] == "SNV" for r in samples[0]["variant_records"])


def test_multisample_genotypes_become_real_carriers(tmp_path):
    path = tmp_path / "cohort.vcf"
    path.write_text("##fileformat=VCFv4.2\\n#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO\\tFORMAT\\tC1\\tC2\\n17\\t100\\t.\\tA\\tG\\t.\\tPASS\\tGENE=TP53\\tGT\\t1/1\\t0/0\\n", encoding="utf-8")
    samples = read_vcf_cohort(path, "case")
    assert {s["sample_id"] for s in samples} == {"C1", "C2"}
    assert samples[0]["variants"] == ["17:100:A:G"]
    assert samples[1]["variants"] == []


def test_indel_is_classified(tmp_path):
    path = tmp_path / "x.vcf"
    path.write_text("#CHROM\\tPOS\\tID\\tREF\\tALT\\tQUAL\\tFILTER\\tINFO\\n1\\t10\\t.\\tAT\\tA\\t.\\tPASS\\t.\\n", encoding="utf-8")
    sample = read_vcf_cohort(path, "control")[0]
    assert sample["variant_records"][0]["variant_type"] == "INDEL"
