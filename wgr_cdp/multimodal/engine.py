"""Dependency-free multimodal WGR-CDP research engine.

Supported normalized feature schema:
patient, group, stage, region, feature_type, value, status

Optional fields: chrom, start, end, assay, depth, tumor_fraction, error_rate,
blood_background, validation_status.
"""

import csv, json, math
from pathlib import Path

RESOLUTIONS = [(5_000_000, "5Mb"), (1_000_000, "1Mb"), (100_000, "100kb"), (10_000, "10kb"), (1_000, "1kb")]
FEATURE_TYPES = {"SNV", "INDEL", "CNV", "SV", "METHYLATION", "MITOCHONDRIAL", "FRAGMENTOMICS"}

def _f(x, default=0.0):
    try: return float(x)
    except (TypeError, ValueError): return default

def load_feature_table(path):
    path=Path(path)
    if not path.exists(): raise ValueError(f"feature table does not exist: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as h:
        rows=list(csv.DictReader(h))
    required={"patient","region","feature_type","value","status"}
    missing=required-set(rows[0]) if rows else required
    if missing: raise ValueError("feature table missing required columns: "+", ".join(sorted(missing)))
    out=[]
    for r in rows:
        x={k:(v.strip() if isinstance(v,str) else v) for k,v in r.items()}
        x["feature_type"]=str(x["feature_type"]).upper()
        x["status"]=str(x["status"]).strip().title()
        if x["feature_type"] not in FEATURE_TYPES: raise ValueError(f"unsupported feature_type: {x['feature_type']}")
        if x["status"] not in {"Detected","Not detected","Data unavailable"}: raise ValueError(f"unsupported status: {x['status']}")
        out.append(x)
    return out

def _parse_region(region):
    s=str(region)
    if ":" not in s or "-" not in s: return None
    chrom, span=s.split(":",1); a,b=span.split("-",1)
    try: return chrom,int(a.replace(",","")),int(b.replace(",",""))
    except ValueError: return None

def region_bins(region, resolution):
    parsed=_parse_region(region)
    if not parsed: return [str(region)]
    chrom,start,end=parsed; size=resolution
    first=start//size; last=max(first,(max(start,end)-1)//size)
    return [f"{chrom}:{i*size+1}-{(i+1)*size}" for i in range(first,last+1)]

def scan_multiresolution(rows):
    result=[]
    for size,label in RESOLUTIONS:
        counts={}
        for r in rows:
            for region in region_bins(r["region"],size):
                k=(label,region,r["feature_type"])
                bucket=counts.setdefault(k,{"resolution":label,"region":region,"feature_type":r["feature_type"],"patients":set(),"detected":0,"total":0})
                bucket["patients"].add(r["patient"])
                bucket["total"]+=1
                if r["status"]=="Detected": bucket["detected"]+=1
        for b in counts.values():
            result.append({**b,"patients":len(b["patients"]),"detect_rate":b["detected"]/b["total"] if b["total"] else 0.0})
    return result

def build_patient_candidate_matrix(rows):
    patients=sorted({r["patient"] for r in rows})
    candidates=sorted({str(r["region"])+"|"+str(r["feature_type"]) for r in rows})
    detected={(r["patient"],str(r["region"])+"|"+str(r["feature_type"])) for r in rows if r["status"]=="Detected"}
    matrix=[]
    for p in patients:
        row={"patient":p}
        for c in candidates: row[c]=1 if (p,c) in detected else 0
        matrix.append(row)
    return matrix

def detectability_curve(tumor_fractions=None, depth=300, error_rate=0.001, min_alt_reads=3):
    fractions=tumor_fractions or [0.5,0.25,0.1,0.05,0.02,0.01,0.005]
    out=[]
    for f in fractions:
        p=max(0.0,min(1.0,f+error_rate))
        prob0=(1-p)**depth
        prob1=depth*p*((1-p)**(depth-1)) if depth else 0
        prob2=(depth*(depth-1)/2)*p*p*((1-p)**max(depth-2,0)) if depth>=2 else 0
        below=sum([prob0,prob1,prob2]) if min_alt_reads==3 else 0
        power=max(0.0,min(1.0,1-below))
        out.append({"tumor_fraction":f,"depth":depth,"error_rate":error_rate,"min_alt_reads":min_alt_reads,"power":power})
    return out

def estimate_lod(depth=300,error_rate=0.001,target_power=0.95,min_alt_reads=3):
    for i in range(1,10001):
        f=i/1_000_000
        if detectability_curve([f],depth,error_rate,min_alt_reads)[0]["power"]>=target_power: return f
    return 0.01

def _group_of(r, metadata):
    return str(r.get("group") or metadata.get(r["patient"],{}).get("group") or "unknown").lower()

def analyze_multimodal_features(rows, metadata=None):
    metadata=metadata or {}
    by_type={}
    for r in rows:
        by_type.setdefault(r["feature_type"],[]).append(r)
    outputs={}
    for ft,items in by_type.items():
        case=[r for r in items if _group_of(r,metadata) in {"case","cancer","tumor"}]
        control=[r for r in items if _group_of(r,metadata) in {"control","healthy","normal"}]
        candidates=sorted({str(r["region"])+"|"+ft for r in items})
        stats=[]
        for c in candidates:
            region=c.rsplit("|",1)[0]
            cdet={r["patient"] for r in case if r["region"]==region and r["status"]=="Detected"}
            hdet={r["patient"] for r in control if r["region"]==region and r["status"]=="Detected"}
            cn=len({r["patient"] for r in case}); hn=len({r["patient"] for r in control})
            cf=len(cdet)/cn if cn else 0; hf=len(hdet)/hn if hn else 0
            subset=[r for r in items if r["region"]==region]
            early=[r for r in subset if str(r.get("stage","")).replace(" ","").lower() in {"i","ii","stagei","stageii","1","2","stage1","stage2"} and r["status"]=="Detected"]
            early_cases={r["patient"] for r in early if _group_of(r,metadata) in {"case","cancer","tumor"}}
            early_stage_fraction=len(early_cases)/len(cdet) if cdet else 0.0
            backgrounds=[_f(r.get("blood_background"),0.0) for r in subset if r.get("blood_background") not in (None,"")]
            detectabilities=[]
            for r in subset:
                tf=_f(r.get("tumor_fraction"),0.0); dp=int(_f(r.get("depth"),300) or 300); er=_f(r.get("error_rate"),0.001)
                if tf>0: detectabilities.append(detectability_curve([tf],dp,er)[0]["power"])
            stats.append({"feature":c,"feature_type":ft,"case_carriers":len(cdet),"control_carriers":len(hdet),"case_n":cn,"control_n":hn,"case_frequency":cf,"control_frequency":hf,"frequency_difference":cf-hf,"specificity":max(0.0,cf-hf),"early_stage_fraction":early_stage_fraction,"blood_background":max(backgrounds) if backgrounds else None,"detectability":sum(detectabilities)/len(detectabilities) if detectabilities else None,"validation_status":next((r.get("validation_status") for r in subset if r.get("validation_status")), "Data unavailable"),"validation_gap":next((r.get("validation_status") for r in subset if r.get("validation_status")), "Data unavailable")=="Data unavailable"})
        outputs[ft]=stats
    return outputs

def categorical_comparison(rows, key):
    groups=sorted({str(r.get(key,"")).strip() for r in rows if str(r.get(key,"")).strip()})
    out=[]
    for g in groups:
        subset=[r for r in rows if str(r.get(key,"")).strip()==g]
        patients=sorted({r["patient"] for r in subset})
        detected=sum(1 for r in subset if r["status"]=="Detected")
        out.append({"grouping":key,"group":g,"patients":len(patients),"features":len(subset),"detected":detected,"detect_rate":detected/len(subset) if subset else 0.0})
    return out

def optimize_panel(matrix, max_k=15, min_coverage=0.0):
    if not matrix: return {"selected":[],"coverage":0.0,"covered_patients":0,"patient_count":0}
    patients=[r["patient"] for r in matrix]; candidates=[k for k in matrix[0] if k!="patient"]
    selected=[]; covered=set()
    while candidates and len(selected)<max_k:
        best=max(candidates,key=lambda c:sum(1 for r in matrix if r.get(c)==1 and r["patient"] not in covered))
        gain={r["patient"] for r in matrix if r.get(best)==1}-covered
        if not gain: break
        selected.append(best); covered |= gain; candidates.remove(best)
        if len(covered)/len(patients)>=min_coverage: break
    return {"selected":selected,"coverage":len(covered)/len(patients),"covered_patients":len(covered),"patient_count":len(patients),"max_k":max_k}

def write_csv(path,rows,fields):
    with open(path,"w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def run_multimodal_analysis(feature_path, output_dir, metadata=None, max_panel_size=15, depth=300, error_rate=0.001):
    rows=load_feature_table(feature_path); output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    by_type=analyze_multimodal_features(rows,metadata); multi=scan_multiresolution(rows); matrix=build_patient_candidate_matrix(rows); panel=optimize_panel(matrix,max_panel_size)
    curve=detectability_curve(depth=depth,error_rate=error_rate); lod=estimate_lod(depth,error_rate)
    write_csv(output/"multimodal_features.csv",rows,list(rows[0].keys()))
    fields=["resolution","region","feature_type","patients","detected","total","detect_rate"]; write_csv(output/"multi_resolution_regions.csv",multi,fields)
    matrix_fields=["patient"]+([k for k in matrix[0] if k!="patient"] if matrix else []); write_csv(output/"patient_candidate_matrix.csv",matrix,matrix_fields)
    stats=[]
    for ft,items in by_type.items(): stats.extend(items)
    if stats: write_csv(output/"multimodal_cohort_comparison.csv",stats,list(stats[0].keys()))
    cohort_rows=categorical_comparison(rows,"group")
    stage_rows=categorical_comparison(rows,"stage")
    if cohort_rows: write_csv(output/"cohort_comparison.csv",cohort_rows,list(cohort_rows[0].keys()))
    if stage_rows: write_csv(output/"stage_comparison.csv",stage_rows,list(stage_rows[0].keys()))
    write_csv(output/"detectability_curve.csv",curve,list(curve[0].keys()))
    (output/"panel.json").write_text(json.dumps(panel,indent=2),encoding="utf-8")
    from .report import write_report
    (output/"lod.json").write_text(json.dumps({"estimated_lod":lod,"depth":depth,"error_rate":error_rate},indent=2),encoding="utf-8")
    result={"feature_types":sorted(by_type),"feature_count":len(rows),"multi_resolution_count":len(multi),"panel":panel,"lod":lod}
    write_report(output,result,rows)
    return result
