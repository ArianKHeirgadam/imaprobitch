from wgr_cdp.annotation_integration.mapper import map_annotation
from wgr_cdp.annotation_integration.pipeline import annotate_variants


def test_annotation_mapping():
    result = map_annotation({
        "gene": "TP53",
        "consequence": "missense_variant",
        "impact": "MODERATE",
        "source": "test",
    })
    assert result["gene"] == "TP53"
    assert result["impact"] == "MODERATE"


def test_annotation_pipeline_with_missing_annotation():
    variants = [{"chrom": "17", "pos": 7579472, "ref": "C", "alt": "T"}]
    result = annotate_variants(variants, lambda _: None)
    assert result[0]["annotation"]["gene"] is None
    assert result[0]["annotation"]["source"] is None


def test_annotation_pipeline_with_adapter():
    variants = [{"chrom": "17", "pos": 7579472, "ref": "C", "alt": "T"}]

    def adapter(variant):
        assert variant["chrom"] == "17"
        return {
            "gene": "TP53",
            "consequence": "missense_variant",
            "impact": "MODERATE",
            "source": "test_adapter",
        }

    result = annotate_variants(variants, adapter)
    assert result[0]["annotation"]["gene"] == "TP53"
    assert result[0]["annotation"]["source"] == "test_adapter"
