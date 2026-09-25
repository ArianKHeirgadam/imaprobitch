"""Quality checks."""


def check_completeness(report):
    if not report.get("run_id"):
        return False

    if report.get("metrics") is None:
        return False

    return True


def check_artifacts(report):
    return isinstance(report.get("artifacts"), list)
