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

def test_gdc_post_retries_transient_tls(monkeypatch):
    from wgr_cdp.data_ingestion import gdc_cohort as g
    calls = {"n": 0}
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"data":{"hits":[],"pagination":{"total":0}}}'
    def fake_open(request, timeout=30):
        calls["n"] += 1
        if calls["n"] < 2:
            raise OSError("transient TLS failure")
        return FakeResponse()
    monkeypatch.setattr(g, "urlopen", fake_open)
    result = g._post_json("cases", {"filters": {}})
    assert calls["n"] == 2
    assert result["data"]["pagination"]["total"] == 0


def test_select_primary_variant_files_chooses_one_gatk_per_case():
    from wgr_cdp.data_ingestion.study_cohort import select_primary_variant_files
    rows = [
        {
            "file_id": "varscan", "file_name": "varscan.vcf.gz",
            "access": "controlled", "data_type": "Annotated Somatic Mutation",
            "data_format": "VCF", "experimental_strategy": "WGS",
            "analysis": {"workflow_type": "VarScan2 Annotation"},
            "cases": [{"case_id": "C1"}],
        },
        {
            "file_id": "mutect", "file_name": "mutect.vcf.gz",
            "access": "controlled", "data_type": "Annotated Somatic Mutation",
            "data_format": "VCF", "experimental_strategy": "WGS",
            "analysis": {"workflow_type": "GATK4 MuTect2 Annotation"},
            "cases": [{"case_id": "C1"}],
        },
        {
            "file_id": "mutectpair", "file_name": "mutectpair.vcf.gz",
            "access": "controlled", "data_type": "Annotated Somatic Mutation",
            "data_format": "VCF", "experimental_strategy": "WGS",
            "analysis": {"workflow_type": "GATK4 MuTect2 Pair"},
            "cases": [{"case_id": "C1"}],
        },
    ]
    out = select_primary_variant_files(
        rows, modality="SNV_INDEL", access="controlled",
        strategy="WGS", case_ids=["C1"]
    )
    assert [x["file_id"] for x in out] == ["mutectpair"]

def test_select_variant_files_accepts_copy_number_variation_category():
    from wgr_cdp.data_ingestion.study_cohort import select_variant_files
    rows = [{
        "file_id": "cnv1", "access": "controlled",
        "data_type": "Copy Number Segment",
        "data_category": "Copy Number Variation",
        "data_format": "TSV", "experimental_strategy": "WGS",
        "cases": [{"case_id": "C1"}],
    }]
    out = select_variant_files(
        rows, modality="CNV", access="controlled",
        strategy="WGS", case_ids=["C1"]
    )
    assert [x["file_id"] for x in out] == ["cnv1"]


def test_gdc_get_query_encodes_nested_filters(monkeypatch):
    from wgr_cdp.data_ingestion import gdc_cohort as g
    calls = {"n": 0, "url": ""}
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b'{"data":{"hits":[],"pagination":{"total":0}}}'
    def fake_open(request, timeout=30):
        calls["n"] += 1
        calls["url"] = request.full_url
        return FakeResponse()
    monkeypatch.setattr(g, "urlopen", fake_open)
    result = g._get_json(
        "cases",
        {
            "filters": {"op": "in", "content": {"field": "project.project_id", "value": ["TCGA-STAD"]}},
            "fields": "case_id,submitter_id",
            "format": "JSON",
            "size": 10,
            "from": 0,
        },
    )
    assert calls["n"] == 1
    assert "filters=" in calls["url"]
    assert "TCGA-STAD" in calls["url"]
    assert result["data"]["pagination"]["total"] == 0


def test_open_study_subset_is_case_limited_and_deterministic():
    from wgr_cdp.data_ingestion.study_cohort import select_open_study_subset
    study = {
        "source_project": "TCGA-STAD",
        "selected_pair_count": 3,
        "selected": [{"case_id": "C1"}, {"case_id": "C2"}, {"case_id": "C3"}],
        "public_wxs_maf_fallback": [
            {
                "file_id": "F3", "file_name": "z.maf.gz", "access": "open",
                "experimental_strategy": "WXS", "data_format": "MAF",
                "cases": [{"case_id": "C3"}],
            },
            {
                "file_id": "F1", "file_name": "a.maf.gz", "access": "open",
                "experimental_strategy": "WXS", "data_format": "MAF",
                "cases": [{"case_id": "C1"}],
            },
            {
                "file_id": "F2", "file_name": "b.maf.gz", "access": "open",
                "experimental_strategy": "WXS", "data_format": "MAF",
                "cases": [{"case_id": "C2"}],
            },
            {
                "file_id": "CTRL", "file_name": "c.maf.gz", "access": "controlled",
                "experimental_strategy": "WXS", "data_format": "MAF",
                "cases": [{"case_id": "C1"}],
            },
        ],
    }
    result = select_open_study_subset(study, limit=2)
    assert result["selected_case_count"] == 2
    assert result["selected_file_count"] == 2
    assert result["selected_case_ids"] == ["C1", "C2"]
    assert [row["file_id"] for row in result["selected_files"]] == ["F1", "F2"]
    assert result["access_policy"] == "open_only"
    assert result["download_scope"] == "subset_only"


def test_open_study_subset_rejects_nonpositive_limit():
    from wgr_cdp.data_ingestion.study_cohort import select_open_study_subset
    try:
        select_open_study_subset({"selected": [], "public_wxs_maf_fallback": []}, limit=0)
    except ValueError as exc:
        assert "greater than zero" in str(exc)
    else:
        raise AssertionError("expected ValueError")
