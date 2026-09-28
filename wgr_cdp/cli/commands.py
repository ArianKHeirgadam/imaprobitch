"""Command implementations for the real WGR-CDP CLI."""

from wgr_cdp.application.analysis import analyze_cohorts
from wgr_cdp.release.health import run_health_check


def run_command(healthy, cancer, output, annotate=False, alpha=0.05, timeout=10):
    return analyze_cohorts(healthy, cancer, output, annotate=annotate, alpha=alpha, timeout=timeout)


def validate_command():
    return run_health_check()


def report_command(output):
    from pathlib import Path
    path = Path(output) / "report.html"
    if not path.exists():
        raise FileNotFoundError(f"report not found: {path}")
    print(path.resolve())
    return {"report": str(path.resolve())}
