"""WGR-CDP Phase 32 research report generation.

Provides JSON and HTML report generation for research-oriented
WGR-CDP analysis results.

The report intentionally presents computational evidence and analysis
results without interpreting them as clinical diagnostic probabilities.
"""

import html
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPORT_TITLE = "WGR-CDP Research Analysis Report"


def _utc_timestamp() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _json_default(value: Any) -> str:
    """Fallback serializer for values not natively supported by json."""
    return str(value)


def build_research_report(results: dict[str, Any]) -> dict[str, Any]:
    """Build the canonical WGR-CDP research report structure.

    Parameters
    ----------
    results:
        Dictionary containing the results produced by the analysis
        pipeline.

    Returns
    -------
    dict
        Structured research report.
    """
    if not isinstance(results, dict):
        raise TypeError("results must be a dictionary")

    return {
        "title": REPORT_TITLE,
        "generated_at": _utc_timestamp(),
        "summary": results.get("summary", {}),
        "analysis": results,
    }


def save_json_report(
    results: dict[str, Any],
    output: str | Path,
) -> Path:
    """Generate and save the research report as JSON.

    Parameters
    ----------
    results:
        Analysis results.
    output:
        Destination JSON file.

    Returns
    -------
    Path
        Path to the generated report.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    report = build_research_report(results)

    output.write_text(
        json.dumps(
            report,
            indent=2,
            default=_json_default,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output


def save_html_report(
    results: dict[str, Any],
    output: str | Path,
) -> Path:
    """Generate and save the research report as an HTML document.

    Parameters
    ----------
    results:
        Analysis results.
    output:
        Destination HTML file.

    Returns
    -------
    Path
        Path to the generated report.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    report = build_research_report(results)

    summary_json = json.dumps(
        report["summary"],
        indent=2,
        default=_json_default,
        ensure_ascii=False,
    )

    analysis_json = json.dumps(
        report["analysis"],
        indent=2,
        default=_json_default,
        ensure_ascii=False,
    )

    generated_at = html.escape(str(report["generated_at"]))

    html_document = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta
        name="viewport"
        content="width=device-width, initial-scale=1"
    >
    <title>{html.escape(REPORT_TITLE)}</title>

    <style>
        body {{
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            color: #222;
        }}

        .container {{
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 24px;
        }}

        .header {{
            background: #ffffff;
            border: 1px solid #d9d9d9;
            border-radius: 8px;
            padding: 28px;
            margin-bottom: 24px;
        }}

        .header h1 {{
            margin-top: 0;
            margin-bottom: 8px;
        }}

        .generated {{
            color: #666;
            font-size: 0.95rem;
        }}

        .section {{
            background: #ffffff;
            border: 1px solid #d9d9d9;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
        }}

        .section h2 {{
            margin-top: 0;
        }}

        pre {{
            background: #f7f7f7;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .footer {{
            color: #777;
            font-size: 0.85rem;
            padding: 8px 0 32px;
        }}
    </style>
</head>

<body>
    <main class="container">

        <header class="header">
            <h1>{html.escape(REPORT_TITLE)}</h1>
            <div class="generated">
                Generated: {generated_at}
            </div>
        </header>

        <section class="section">
            <h2>Summary</h2>
            <pre>{html.escape(summary_json)}</pre>
        </section>

        <section class="section">
            <h2>Analysis Results</h2>
            <pre>{html.escape(analysis_json)}</pre>
        </section>

        <div class="footer">
            WGR-CDP research framework report.
            Results represent computational research evidence and
            should not be interpreted as clinical diagnostic probabilities.
        </div>

    </main>
</body>
</html>
"""

    output.write_text(
        html_document,
        encoding="utf-8",
    )

    return output