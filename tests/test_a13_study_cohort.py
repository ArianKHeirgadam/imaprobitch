from wgr_cdp.data_ingestion.study_cohort import select_paired_tcga_cases, select_open_variant_files

def test_select_paired_tcga_cases_prefers_solid_normal():
    manifest = {"project_id":"TCGA-STAD","samples":[
        {"case_id":"C1","sample_id":"T1","sample_type":"Primary Tumor","tissue_type":"Tumor"},
        {"case_id":"C1","sample_id":"N1","sample_type":"Solid Tissue Normal","tissue_type":"Normal"},
        {"case_id":"C1","sample_id":"BN1","sample_type":"Blood Derived Normal","tissue_type":"Normal"},
        {"case_id":"C2","sample_id":"T2","sample_type":"Primary Tumor","tissue_type":"Tumor"},
    ]}
    result=select_paired_tcga_cases(manifest)
    assert result["selected_pair_count"] == 1
    assert result["selected"][0]["tumor_sample"]["sample_id"] == "T1"
    assert result["selected"][0]["normal_sample"]["sample_id"] == "N1"
    assert result["excluded_cases"][0]["case_id"] == "C2"

def test_select_open_snv_files():
    rows = [
        {"access":"open","data_type":"Masked Somatic Mutation","data_format":"MAF","experimental_strategy":"WXS","file_id":"b"},
        {"access":"controlled","data_type":"Raw Simple Somatic Mutation","data_format":"VCF","experimental_strategy":"WXS","file_id":"c"},
        {"access":"open","data_type":"Gene Expression Quantification","data_format":"TSV","experimental_strategy":"RNA-Seq","file_id":"a"},
    ]
    out=select_open_variant_files(rows)
    assert [x["file_id"] for x in out] == ["b"]

def test_select_variant_files_can_target_wgs_controlled_case():
    rows = [{
        "file_id": "wgs1", "access": "controlled", "data_type": "Raw Simple Somatic Mutation",
        "data_format": "VCF", "experimental_strategy": "WGS",
        "cases": [{"case_id": "C1"}],
    }, {
        "file_id": "wgs2", "access": "controlled", "data_type": "Raw Simple Somatic Mutation",
        "data_format": "VCF", "experimental_strategy": "WGS",
        "cases": [{"case_id": "C2"}],
    }]
    from wgr_cdp.data_ingestion.study_cohort import select_variant_files
    out = select_variant_files(rows, access="controlled", strategy="WGS", case_ids=["C1"])
    assert [x["file_id"] for x in out] == ["wgs1"]

def test_classify_blood_normal_before_generic_normal_tissue_type():
    from wgr_cdp.data_ingestion.study_cohort import _sample_class
    assert _sample_class({
        "sample_type": "Blood Derived Normal",
        "tissue_type": "Normal",
    }) == "NORMAL_BLOOD"
    assert _sample_class({
        "sample_type": "Solid Tissue Normal",
        "tissue_type": "Normal",
    }) == "NORMAL_SOLID"
