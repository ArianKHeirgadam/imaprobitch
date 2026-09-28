from wgr_cdp.data_ingestion.vcf import read_vcf
from wgr_cdp.data_ingestion.normalize import normalize_variant


def test_read_vcf(tmp_path):
    path = tmp_path / "sample.vcf"
    path.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        "1\t12345\trs1\tA\tG\t99\tPASS\tDP=20\n",
        encoding="utf-8",
    )
    records = read_vcf(path)
    assert len(records) == 1
    assert records[0]["pos"] == 12345
    assert records[0]["alt"] == ["G"]


def test_normalize_variant():
    result = normalize_variant({"chrom": 1, "pos": 10, "ref": "a", "alt": ["g", "t"]})
    assert result == {"chrom": "1", "pos": 10, "ref": "A", "alt": ["G", "T"]}
