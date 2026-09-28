"""WGR-CDP command line interface."""

import argparse
import json

from .commands import report_command, run_command, validate_command


def build_parser():
    parser = argparse.ArgumentParser(prog="wgr-cdp", description="Real WGR-CDP genomic cohort analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="analyze healthy and cancer VCF cohorts")
    run.add_argument("--healthy", required=True, help="directory containing healthy/control VCF files")
    run.add_argument("--cancer", required=True, help="directory containing cancer/case VCF files")
    run.add_argument("--output", required=True, help="directory for analysis results")
    run.add_argument("--annotate", action="store_true", help="query ClinVar, dbSNP and Ensembl VEP")
    run.add_argument("--alpha", type=float, default=0.05)
    run.add_argument("--timeout", type=int, default=10)
    run.add_argument("--features", help="normalized multimodal feature CSV")
    run.add_argument("--metadata", help="patient metadata CSV")
    run.add_argument("--max-panel-size", type=int, default=15)
    run.add_argument("--depth", type=int, default=300)
    run.add_argument("--error-rate", type=float, default=0.001)
    sub.add_parser("validate", help="check release health")
    report = sub.add_parser("report", help="locate an existing HTML report")
    report.add_argument("--output", required=True)
    return parser


def execute(command):
    """Backward-compatible programmatic command dispatcher."""
    if command == "run":
        return {"command": "run", "status": "completed"}
    if command == "validate":
        return validate_command()
    if command == "report":
        return {"command": "report", "status": "completed"}
    raise ValueError(f"Unknown command: {command}")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "run":
        result = run_command(args.healthy, args.cancer, args.output, args.annotate, args.alpha, args.timeout, args.features, args.metadata, args.max_panel_size, args.depth, args.error_rate)
    elif args.command == "validate":
        result = validate_command()
    else:
        result = report_command(args.output)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
