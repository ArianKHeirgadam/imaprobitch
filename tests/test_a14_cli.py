def test_cli_parser_exposes_snv_indel_detect():
    from wgr_cdp.cli.main import build_parser
    args = build_parser().parse_args([
        "snv-indel-detect",
        "--cancer", "cancer",
        "--healthy", "healthy",
        "--output", "out",
        "--min-depth", "20",
        "--min-vaf", "0.05",
    ])
    assert args.command == "snv-indel-detect"
    assert args.min_depth == 20
    assert args.min_vaf == 0.05


def test_cli_parser_exposes_real_snv_indel_validation():
    from wgr_cdp.cli.main import build_parser
    args = build_parser().parse_args([
        "snv-indel-validate",
        "--cancer", "normalized",
        "--output", "out",
    ])
    assert args.command == "snv-indel-validate"
    assert args.cancer == "normalized"
