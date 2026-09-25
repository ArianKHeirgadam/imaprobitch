"""Quality gate execution."""

from .schema import validate_schema
from .checks import check_completeness, check_artifacts


def run_quality_gate(report):
    checks = {
        "schema": validate_schema(report),
        "completeness": check_completeness(report),
        "artifacts": check_artifacts(report),
    }

    return {
        "passed": all(checks.values()),
        "checks": checks,
    }
