"""ClinVar adapter interface."""


def annotate_from_clinvar(variant_id):
    return {
        "source": "ClinVar",
        "variant_id": variant_id,
        "classification": None,
        "status": "adapter_ready",
    }
