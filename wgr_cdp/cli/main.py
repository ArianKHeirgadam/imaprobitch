"""WGR-CDP command line interface."""
import argparse, json
from .commands import report_command, run_command, validate_command, intake_command, inventory_command, acquire_command, register_command, data_plan_command, one_kg_manifest_command, reference_acquire_command, maf_to_vcf_command, one_kg_select_command
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
    run.add_argument("--background",help="blood-background / PoN CSV/TSV")
    run.add_argument("--max-background",type=float,default=1.0,help="maximum allowed background frequency")
    run.add_argument("--cohort-metadata",help="optional sample-level design metadata CSV for batch/platform/confounder audit")
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
    dp=sub.add_parser("data-plan",help="write the recommended TCGA-STAD/1000G/GTEx real-data acquisition plan")
    dp.add_argument("--output",required=True)
    dp.add_argument("--healthy-samples",type=int,default=250)
    dp.add_argument("--no-gtex",action="store_true")
    kg=sub.add_parser("1000g-manifest",help="write public 1000 Genomes 30x GRCh38 download manifest")
    kg.add_argument("--output",required=True)
    kg.add_argument("--samples",type=int,default=250)
    kg.add_argument("--chromosomes",help="comma-separated chromosome list, e.g. 1,2,X")
    ra=sub.add_parser("reference-acquire",help="download URLs from a reference manifest")
    ra.add_argument("--manifest",required=True)
    ra.add_argument("--output",required=True)
    ra.add_argument("--limit",type=int)
    ra.add_argument("--timeout",type=int,default=60)
    mt=sub.add_parser("maf-to-vcf",help="convert a GDC masked somatic MAF into per-sample adapter VCFs")
    mt.add_argument("--input",required=True)
    mt.add_argument("--output",required=True)
    ss=sub.add_parser("1000g-select",help="select a deterministic population-balanced 1000G sample list")
    ss.add_argument("--panel",required=True)
    ss.add_argument("--output",required=True)
    ss.add_argument("--samples",type=int,default=250)
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
        result=run_command(args.healthy,args.cancer,args.output,args.annotate,args.alpha,args.timeout,args.features,args.metadata,args.max_panel_size,args.depth,args.error_rate,args.cnv,args.literature_search,args.validation_candidates,args.bootstrap,args.background,args.max_background,args.cohort_metadata)
    elif args.command=="data-plan":
        result=data_plan_command(args.output,args.healthy_samples,not args.no_gtex)
    elif args.command=="1000g-manifest":
        result=one_kg_manifest_command(args.output,args.samples,args.chromosomes)
    elif args.command=="reference-acquire":
        result=reference_acquire_command(args.manifest,args.output,args.limit,args.timeout)
    elif args.command=="maf-to-vcf":
        result=maf_to_vcf_command(args.input,args.output)
    elif args.command=="1000g-select":
        result=one_kg_select_command(args.panel,args.output,args.samples)
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
    elif args.command=="data-plan":
        result=data_plan_command(args.output,args.healthy_samples,not args.no_gtex)
    elif args.command=="1000g-manifest":
        result=one_kg_manifest_command(args.output,args.samples,args.chromosomes)
    elif args.command=="reference-acquire":
        result=reference_acquire_command(args.manifest,args.output,args.limit,args.timeout)
    elif args.command=="maf-to-vcf":
        result=maf_to_vcf_command(args.input,args.output)
    elif args.command=="1000g-select":
        result=one_kg_select_command(args.panel,args.output,args.samples)
    else:
        result=report_command(args.output)
    print(json.dumps(result,indent=2,default=str)); return 0


if __name__=="__main__":
    raise SystemExit(main())
