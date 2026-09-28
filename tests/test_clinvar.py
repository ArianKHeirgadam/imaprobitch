import json

from wgr_cdp.clinvar import ClinVarClient, clinvar_adapter
from wgr_cdp.annotation_integration.pipeline import annotate_variants


def test_clinvar_lookup_uses_eutils_and_maps_result():
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        if "esearch.fcgi" in url:
            return json.dumps({"esearchresult": {"idlist": ["65533"]}})
        return json.dumps({
            "result": {
                "65533": {
                    "gene_symbol": "TP53",
                    "variant_type": "single nucleotide variant",
                    "clinical_significance": "Pathogenic",
                    "accession": "VCV000065533",
                }
            }
        })

    client = ClinVarClient(request_get=fake_get)
    result = client.lookup_variant({
        "chrom": "17",
        "pos": 7579472,
        "ref": "C",
        "alt": "T",
    })

    assert result["gene"] == "TP53"
    assert result["impact"] == "Pathogenic"
    assert result["source"] == "clinvar"
    assert result["clinvar_id"] == "65533"
    assert len(calls) == 2


def test_clinvar_missing_variant_is_stable():
    def fake_get(url, timeout):
        return json.dumps({"esearchresult": {"idlist": []}})

    client = ClinVarClient(request_get=fake_get)
    result = client.lookup_variant({
        "chrom": "17",
        "pos": 1,
        "ref": "A",
        "alt": "T",
    })

    assert result["source"] == "clinvar"
    assert result["gene"] is None


def test_clinvar_adapter_integrates_with_pipeline():
    def fake_get(url, timeout):
        if "esearch.fcgi" in url:
            return json.dumps({"esearchresult": {"idlist": ["1"]}})
        return json.dumps({
            "result": {
                "1": {
                    "gene_symbol": "TP53",
                    "variant_type": "single nucleotide variant",
                    "clinical_significance": "Pathogenic",
                }
            }
        })

    variants = [{"chrom": "17", "pos": 7579472, "ref": "C", "alt": "T"}]
    result = annotate_variants(
        variants,
        clinvar_adapter(ClinVarClient(request_get=fake_get)),
    )

    assert result[0]["annotation"]["gene"] == "TP53"
    assert result[0]["annotation"]["source"] == "clinvar"
