"""WGR-CDP command line interface."""
import argparse, json
from .commands import report_command, run_command, validate_command, intake_command, inventory_command, acquire_command, register_command
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
    intake=sub.add_parser("intake",help="discover released GDC project metadata without downloading data")
    intake.add_argument("--project",default="TCGA-STAD")
    intake.add_argument("--output",required=True)
    intake.add_argument("--file-access",choices=["open","controlled"])
    inv=sub.add_parser("inventory",help="build a GDC file acquisition manifest")
    inv.add_argument("--project",default="TCGA-STAD")
    inv.add_argument("--output",required=True)
    inv.add_argument("--access",choices=["open","controlled"])
    inv.add_argument("--category")
    inv.add_argument("--strategy")
    inv.add_argument("--format")
    inv.add_argument("--modality",action="append")
    inv.add_argument("--max-files",type=int)
    acq=sub.add_parser("acquire",help="download and checksum-verify files from an A11 manifest")
    acq.add_argument("--manifest",required=True)
    acq.add_argument("--output",required=True)
    acq.add_argument("--token")
    acq.add_argument("--limit",type=int)
    reg=sub.add_parser("register",help="register verified local files from an A11 manifest")
    reg.add_argument("--manifest",required=True)
    reg.add_argument("--root",required=True)
    reg.add_argument("--output",required=True)
    cohort=sub.add_parser("cohort",help="build a real GDC case/sample/variant-file cohort manifest")
    cohort.add_argument("--project",default="TCGA-STAD")
    cohort.add_argument("--output",required=True)
    cohort.add_argument("--access",choices=["open","controlled"])
    cohort.add_argument("--timeout",type=int,default=30)
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
    if command=="intake": return {"command":"intake","status":"completed"}
    if command=="inventory": return {"command":"inventory","status":"completed"}
    if command=="acquire": return {"command":"acquire","status":"completed"}
    if command=="register": return {"command":"register","status":"completed"}
    if command=="cohort": return {"command":"cohort","status":"completed"}
    raise ValueError(f"Unknown command: {command}")


def main(argv=None):
    args=build_parser().parse_args(argv)
    if args.command=="run":
        result=run_command(args.healthy,args.cancer,args.output,args.annotate,args.alpha,args.timeout,args.features,args.metadata,args.max_panel_size,args.depth,args.error_rate,args.cnv,args.literature_search,args.validation_candidates,args.bootstrap)
    elif args.command=="validate":
        result=validate_command()
    elif args.command=="release":
        result=release_readiness()
    elif args.command=="intake":
        result=intake_command(args.project,args.output,args.file_access)
    elif args.command=="inventory":
        result=inventory_command(args.project,args.output,args.access,args.category,args.strategy,args.format,args.modality,args.max_files)
    elif args.command=="acquire":
        result=acquire_command(args.manifest,args.output,args.token,args.limit)
    elif args.command=="register":
        result=register_command(args.manifest,args.root,args.output)
    else:
        result=report_command(args.output)
    print(json.dumps(result,indent=2,default=str)); return 0


if __name__=="__main__":
    raise SystemExit(main())
