"""WGR-CDP command line interface."""
import argparse, json
from .commands import report_command, run_command, validate_command
from wgr_cdp.release.reproducibility import release_readiness


def build_parser():
    parser=argparse.ArgumentParser(prog="wgr-cdp",description="Real WGR-CDP genomic cohort analysis")
    sub=parser.add_subparsers(dest="command",required=True)
    run=sub.add_parser("run",help="analyze healthy and cancer cohorts")
    run.add_argument("--healthy",required=True)
    run.add_argument("--cancer",required=True)
    run.add_argument("--output",required=True)
    run.add_argument("--annotate",action="store_true")
    run.add_argument("--alpha",type=float,default=0.05)
    run.add_argument("--timeout",type=int,default=10)
    run.add_argument("--features")
    run.add_argument("--cnv",help="CNV segment CSV/TSV")
    run.add_argument("--metadata")
    run.add_argument("--max-panel-size",type=int,default=15)
    run.add_argument("--depth",type=int,default=300)
    run.add_argument("--error-rate",type=float,default=0.001)
    run.add_argument("--literature-search",action="store_true",help="query literature sources for candidate evidence")
    run.add_argument("--validation-candidates",help="optional independent validation candidate CSV")
    run.add_argument("--bootstrap",type=int,default=200)
    sub.add_parser("validate",help="check release health")
    sub.add_parser("release",help="check release and reproducibility readiness")
    report=sub.add_parser("report",help="locate an existing HTML report")
    report.add_argument("--output",required=True)
    return parser


def execute(command):
    if command=="run": return {"command":"run","status":"completed"}
    if command=="validate":
        return {"command":"validate",**validate_command()}
    if command=="release":
        return {"command":"release",**release_readiness()}
    if command=="report": return {"command":"report","status":"completed"}
    raise ValueError(f"Unknown command: {command}")


def main(argv=None):
    args=build_parser().parse_args(argv)
    if args.command=="run":
        result=run_command(args.healthy,args.cancer,args.output,args.annotate,args.alpha,args.timeout,args.features,args.metadata,args.max_panel_size,args.depth,args.error_rate,args.cnv,args.literature_search,args.validation_candidates,args.bootstrap)
    elif args.command=="validate":
        result=validate_command()
    elif args.command=="release":
        result=release_readiness()
    else:
        result=report_command(args.output)
    print(json.dumps(result,indent=2,default=str)); return 0


if __name__=="__main__":
    raise SystemExit(main())
