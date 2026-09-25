from wgr_cdp.reference.chromosome_map import normalize_chromosome
from wgr_cdp.reference.coordinate_validator import validate_coordinate


def test_chromosome_normalization():
    assert normalize_chromosome("chr1") == "1"


def test_coordinate_validation():
    assert validate_coordinate("1", 12345, "GRCh38")
    assert not validate_coordinate("1", -1, "GRCh38")
