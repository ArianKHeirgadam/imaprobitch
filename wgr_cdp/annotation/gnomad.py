"""gnomAD adapter interface."""


def annotate_from_gnomad(variant_id):
    return {
        "source": "gnomAD",
        "variant_id": variant_id,
        "status": "adapter_ready",
    }
