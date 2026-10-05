import pytest

from wgr_cdp.cli.main import execute


def test_cli_commands():
    run_result = execute("run")
    assert run_result["status"] == "completed"
    assert "c09" in run_result
    assert "c09_robustness" in run_result["c09"]["artifacts"]
    assert execute("validate")["command"] == "validate"
    assert execute("release")["command"] == "release"
    assert execute("release")["scientific_results"] == "CONDITIONAL"
    assert execute("report")["command"] == "report"
    assert execute("intake")["command"] == "intake"
    assert execute("inventory")["command"] == "inventory"
    assert execute("acquire")["command"] == "acquire"
    assert execute("register")["command"] == "register"
    assert execute("cohort")["command"] == "cohort"


def test_unknown_cli_command():
    with pytest.raises(ValueError):
        execute("unknown")


def test_cli_accepts_blood_background_and_max_background():
    from wgr_cdp.cli.main import build_parser
    args = build_parser().parse_args([
        "run", "--healthy", "healthy.vcf", "--cancer", "cancer.vcf",
        "--output", "results", "--background", "background.csv",
        "--max-background", "0.10",
    ])
    assert args.background == "background.csv"
    assert args.max_background == 0.10
