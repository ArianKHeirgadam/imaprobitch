from wgr_cdp.cli.main import build_parser

def test_real_data_commands_parse():
    assert build_parser().parse_args(["data-plan", "--output", "x.json"]).command == "data-plan"
    assert build_parser().parse_args(["1000g-manifest", "--output", "x.json"]).command == "1000g-manifest"
    assert build_parser().parse_args(["1000g-select", "--panel", "p.txt", "--output", "s.txt"]).command == "1000g-select"
    assert build_parser().parse_args(["1000g-subset", "--input", "a.vcf.gz", "--samples", "s.txt", "--output", "b.vcf.gz"]).command == "1000g-subset"
    assert build_parser().parse_args(["maf-to-vcf", "--input", "x.maf.gz", "--output", "vcf"]).command == "maf-to-vcf"
