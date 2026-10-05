from pathlib import Path


def test_phase32_report_generation(tmp_path):
    from wgr_cdp.reporting.research_report import (
        save_html_report,
        save_json_report,
    )

    data = {
        "summary": {
            "samples": 10
        }
    }

    html = save_html_report(
        data,
        tmp_path / "report.html"
    )

    js = save_json_report(
        data,
        tmp_path / "report.json"
    )

    assert html.exists()
    assert js.exists()
