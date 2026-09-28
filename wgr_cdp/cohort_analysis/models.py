"""Stable cohort input normalization."""


VALID_GROUPS = {"case", "control"}


def normalize_cohort(samples):
    """Normalize sample records into a stable case/control representation.

    Each sample must contain:
      - sample_id
      - group: case or control
      - variants: iterable of variant keys

    Optional fields are preserved so downstream cohort analyses can operate on
    annotated variant records without losing information during normalization.
    """
    normalized = []

    for sample in samples or []:
        sample_id = sample.get("sample_id")
        group = str(sample.get("group", "")).lower()

        if not sample_id:
            raise ValueError("sample_id is required")
        if group not in VALID_GROUPS:
            raise ValueError("group must be 'case' or 'control'")

        variants = list(dict.fromkeys(sample.get("variants") or []))

        item = {
            "sample_id": str(sample_id),
            "group": group,
            "variants": variants,
        }

        if "variant_records" in sample:
            item["variant_records"] = list(sample.get("variant_records") or [])

        normalized.append(item)

    return normalized
