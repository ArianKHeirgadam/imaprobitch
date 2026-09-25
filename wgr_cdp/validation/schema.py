"""Report schema validation."""


REQUIRED_REPORT_FIELDS = [
    "run_id",
    "summary",
    "metrics",
    "artifacts",
]


def validate_schema(report):
    return all(field in report for field in REQUIRED_REPORT_FIELDS)
