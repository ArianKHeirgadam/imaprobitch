from wgr_cdp.variants.models import VariantRecord, validate_variant


def test_snv_representation():
    record = VariantRecord(
        chromosome="1",
        position=100,
        variant_type="SNV",
        reference="A",
        alternate="T",
    )

    assert validate_variant(record)


def test_invalid_variant_type():
    record = VariantRecord(
        chromosome="1",
        position=100,
        variant_type="UNKNOWN",
        reference="A",
        alternate="T",
    )

    assert not validate_variant(record)
