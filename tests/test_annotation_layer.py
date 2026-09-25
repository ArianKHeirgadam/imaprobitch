from wgr_cdp.annotation.evidence import AnnotationEvidence
from wgr_cdp.annotation.clinvar import annotate_from_clinvar
from wgr_cdp.annotation.cosmic import annotate_from_cosmic
from wgr_cdp.annotation.gnomad import annotate_from_gnomad


def test_evidence_model():
    evidence = AnnotationEvidence(
        source="ClinVar",
        variant_id="var_001"
    )
    assert evidence.source == "ClinVar"


def test_annotation_adapters():
    assert annotate_from_clinvar("var_001")["status"] == "adapter_ready"
    assert annotate_from_cosmic("var_001")["status"] == "adapter_ready"
    assert annotate_from_gnomad("var_001")["status"] == "adapter_ready"
