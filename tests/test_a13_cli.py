from wgr_cdp.cli.main import build_parser

def test_study_cohort_command_parses():
    args = build_parser().parse_args([
        "study-cohort", "--project", "TCGA-STAD", "--output", "results/study.json"
    ])
    assert args.command == "study-cohort"
    assert args.project == "TCGA-STAD"
