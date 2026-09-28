import json

from wgr_cdp.functional_evidence import (
    VepClient,
    add_functional_evidence,
    vep_adapter,
)


def test_vep_maps_transcript_and_regulatory_evidence():
    def fake_get(url, timeout):
        return json.dumps([{
            "transcript_consequences": [{
                "gene_symbol": "TP53",
                "gene_id": "ENSG00000141510",
                "transcript_id": "ENST00000269305",
                "consequence_terms": ["missense_variant"],
                "impact": "MODERATE",
                "amino_acids": "P/L",
            }],
            "regulatory_feature_consequences": [{
                "consequence_terms": ["regulatory_region_variant"]
            }],
        }])

    client = VepClient(request_get=fake_get)
    result = client.annotate_variant({
        "chrom": "17",
        "pos": 7579472,
        "ref": "C",
        "alt": "T",
    })

    assert result["source"] == "ensembl_vep"
    assert result["gene"] == "TP53"
    assert result["consequence"] == "missense_variant"
    assert result["impact"] == "MODERATE"
    assert result["transcript"] == "ENST00000269305"
    assert result["protein_change"] == "P/L"
    assert result["regulatory_consequence"] == "regulatory_region_variant"


def test_vep_missing_result_is_stable():
    def fake_get(url, timeout):
        return "[]"

    result = VepClient(request_get=fake_get).annotate_variant({
        "chrom": "1",
        "pos": 1,
        "ref": "A",
        "alt": "T",
    })

    assert result["source"] == "ensembl_vep"
    assert result["gene"] is None
    assert result["consequence"] is None


def test_functional_evidence_pipeline_uses_adapter():
    def fake_get(url, timeout):
        return json.dumps([{
            "transcript_consequences": [{
                "gene_symbol": "TP53",
                "transcript_id": "ENST00000269305",
                "consequence_terms": ["missense_variant"],
                "impact": "MODERATE",
            }]
        }])

    variants = [{
        "chrom": "17",
        "pos": 7579472,
        "ref": "C",
        "alt": "T",
    }]

    result = add_functional_evidence(
        variants,
        vep_adapter(VepClient(request_get=fake_get)),
    )

    evidence = result[0]["functional_evidence"]
    assert evidence["gene"] == "TP53"
    assert evidence["consequence"] == "missense_variant"
    assert evidence["source"] == "ensembl_vep"


def test_functional_evidence_does_not_mutate_variant():
    variant = {
        "chrom": "17",
        "pos": 7579472,
        "ref": "C",
        "alt": "T",
    }

    result = add_functional_evidence(
        [variant],
        lambda _: {
            "source": "test",
            "gene": "TP53",
            "consequence": "missense_variant",
        },
    )

    assert "functional_evidence" not in variant
    assert result[0]["chrom"] == "17"
    assert result[0]["functional_evidence"]["gene"] == "TP53"
