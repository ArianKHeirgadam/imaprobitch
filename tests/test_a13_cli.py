from wgr_cdp.cli.main import build_parser

def test_study_cohort_command_parses():
    args = build_parser().parse_args([
        "study-cohort", "--project", "TCGA-STAD", "--output", "results/study.json"
    ])
    assert args.command == "study-cohort"
    assert args.project == "TCGA-STAD"
    assert args.strategy == "WGS"


def test_study_acquisition_manifest_command_parses():
    args = build_parser().parse_args([
        "study-acquisition-manifest",
        "--study", "results/tcga_stad_study.json",
        "--output", "results/tcga_stad_acquisition.json",
    ])
    assert args.command == "study-acquisition-manifest"
    assert args.study.endswith("tcga_stad_study.json")
    assert args.no_snv is False
    assert args.no_cnv is False
    assert args.public_fallback is False


def test_open_study_acquisition_manifest_parses():
    args = build_parser().parse_args([
        "open-study-acquisition-manifest",
        "--study", "results/tcga_stad_study.json",
        "--output", "results/tcga_stad_open_acquisition.json",
    ])
    assert args.command == "open-study-acquisition-manifest"
    assert args.study.endswith("tcga_stad_study.json")
