from pathlib import Path

def validate_dataset(dataset):
    errors = []

    if not dataset.samples:
        errors.append("No samples found")

    groups = dataset.groups()

    if "cancer" not in groups:
        errors.append("Cancer group missing")

    if "healthy" not in groups:
        errors.append("Healthy group missing")

    ids = [s.sample_id for s in dataset.samples]

    if len(ids) != len(set(ids)):
        errors.append("Duplicate sample ids")

    for sample in dataset.samples:
        if sample.vcf and not Path(sample.vcf).exists():
            errors.append(f"Missing VCF: {sample.vcf}")

        if sample.cnv and not Path(sample.cnv).exists():
            errors.append(f"Missing CNV: {sample.cnv}")

    return {
        "valid": len(errors) == 0,
        "samples": len(dataset.samples),
        "groups": groups,
        "errors": errors
    }
