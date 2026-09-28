"""Final release validation report."""


def build_release_report(health_result, test_count=None):
    """Build a machine-readable release summary."""
    report = {
        "release": health_result.get("release"),
        "passed": bool(health_result.get("passed")),
        "checks": dict(health_result.get("checks", {})),
    }

    if test_count is not None:
        report["test_count"] = int(test_count)

    return report
