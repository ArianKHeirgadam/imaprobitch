import pytest

from wgr_cdp.cli.main import execute


def test_cli_commands():
    assert execute("run")["status"] == "completed"
    assert execute("validate")["command"] == "validate"
    assert execute("release")["command"] == "release"
    assert execute("release")["scientific_results"] == "CONDITIONAL"
    assert execute("report")["command"] == "report"
    assert execute("intake")["command"] == "intake"
    assert execute("inventory")["command"] == "inventory"
    assert execute("acquire")["command"] == "acquire"
    assert execute("register")["command"] == "register"
    assert execute("cohort")["command"] == "cohort"
    assert execute("normalize-vcf")["command"] == "normalize-vcf"
    assert execute("normalize-vcf-batch")["command"] == "normalize-vcf-batch"


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


def test_cli_accepts_reference_aware_normalization():
    from wgr_cdp.cli.main import build_parser

    args = build_parser().parse_args([
        "normalize-vcf-batch",
        "--input", "vcfs",
        "--output", "normalized",
        "--reference", "GRCh38.fa",
        "--reference-build", "GRCh38",
        "--pattern", "*.vcf",
    ])
    assert args.reference == "GRCh38.fa"
    assert args.reference_build == "GRCh38"
    assert args.pattern == "*.vcf"
