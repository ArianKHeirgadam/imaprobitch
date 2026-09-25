"""Report generation layer."""

from .templates import DEFAULT_TEMPLATE
from .formatter import format_report


def generate_report(run_id, summary=None, metrics=None, artifacts=None):
    report = DEFAULT_TEMPLATE.copy()

    report["run_id"] = run_id
    report["summary"] = summary or {}
    report["metrics"] = metrics or {}
    report["artifacts"] = artifacts or []

    return format_report(report)
