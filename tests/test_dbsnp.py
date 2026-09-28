import json

from wgr_cdp.annotation_integration.pipeline import annotate_variants
from wgr_cdp.dbsnp import DbSnpClient, dbsnp_adapter


def test_dbsnp_lookup_resolves_vcf_to_rsid():
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        if "/contextuals" in url:
            return json.dumps({
                "data": {
                    "spdis": [{
                        "seq_id": "NC_000017.11",
                        "position": 7579471,
                        "deleted_sequence": "C",
                        "inserted_sequence": "T",
                    }]
                }
            })
        if "/rsids" in url:
            return json.dumps({"data": {"rsids": ["12345"]}})
        return json.dumps({
            "refsnp_id": "12345",
            "primary_snapshot_data": {"variant_type": "snv"},
        })

    client = DbSnpClient(request_get=fake_get)
    result = client.lookup_variant({
        "chrom": "17",
        "pos": 7579472,
        "ref": "C",
        "alt": "T",
    })

    assert result["source"] == "dbsnp"
    assert result["dbsnp_rsids"] == ["rs12345"]
    assert result["dbsnp_ref_snp_id"] == "rs12345"
    assert result["dbsnp_variant_type"] == "snv"
    assert len(calls) == 3


def test_dbsnp_missing_variant_is_stable():
    def fake_get(url, timeout):
        return json.dumps({"data": {"spdis": []}})

    client = DbSnpClient(request_get=fake_get)
    result = client.lookup_variant({
        "chrom": "1",
        "pos": 1,
        "ref": "A",
        "alt": "T",
    })

    assert result["source"] == "dbsnp"
    assert result["dbsnp_rsids"] == []
    assert result["dbsnp_variant_type"] is None


def test_dbsnp_adapter_integrates_with_pipeline():
    def fake_get(url, timeout):
        if "/contextuals" in url:
            return json.dumps({
                "data": {
                    "spdis": [{
                        "seq_id": "NC_000017.11",
                        "position": 7579471,
                        "deleted_sequence": "C",
                        "inserted_sequence": "T",
                    }]
                }
            })
        if "/rsids" in url:
            return json.dumps({"data": {"rsids": ["12345"]}})
        return json.dumps({
            "primary_snapshot_data": {"variant_type": "snv"}
        })

    variants = [{
        "chrom": "17",
        "pos": 7579472,
        "ref": "C",
        "alt": "T",
    }]
    result = annotate_variants(
        variants,
        dbsnp_adapter(DbSnpClient(request_get=fake_get)),
    )

    assert result[0]["annotation"]["source"] == "dbsnp"
    assert result[0]["annotation"]["dbsnp_rsids"] == ["rs12345"]
