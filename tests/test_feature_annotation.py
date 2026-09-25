from wgr_cdp.variants.models import VariantRecord
from wgr_cdp.features.annotation import annotate_variant, feature_dict


def test_variant_annotation():
    record = VariantRecord(
        chromosome="1",
        position=1000,
        variant_type="SNV",
        reference="A",
        alternate="T",
        vaf=0.25,
    )

    feature = annotate_variant(record)

    assert feature.variant_type == "SNV"
    assert feature.vaf == 0.25


def test_feature_export():
    record = VariantRecord(
        chromosome="2",
        position=2000,
        variant_type="INDEL",
        reference="A",
        alternate="AT",
    )

    output = feature_dict(annotate_variant(record))

    assert output["chromosome"] == "2"
