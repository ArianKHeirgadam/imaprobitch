"""COSMIC adapter interface."""


def annotate_from_cosmic(variant_id):
    return {
        "source": "COSMIC",
        "variant_id": variant_id,
        "status": "adapter_ready",
    }
