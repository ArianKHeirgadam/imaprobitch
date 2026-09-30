"""Feature-aware exact and coarse-to-fine WGR-CDP scanning."""
from collections import defaultdict
from .statistics import fisher_exact_2x2, benjamini_hochberg

RESOLUTIONS=(5_000_000,1_000_000,100_000,10_000,1_000,1)
LABELS={5_000_000:"5Mb",1_000_000:"1Mb",100_000:"100kb",10_000:"10kb",1_000:"1kb",1:"base"}

def _parts(region):
    chrom,span=str(region).split(":",1); start,end=span.split("-",1); return chrom,int(start),int(end)

def _bin(region,size):
    chrom,start,end=_parts(region); first=((start-1)//size)*size+1; last=((max(start,end)-1)//size)*size+1
    return [f"{chrom}:{x}-{x+size-1}" for x in range(first,last+1,size)]

def _group(r): return str(r.get("group","")).lower()
def _patients(rows,groups): return {str(r["patient"]) for r in rows if _group(r) in groups}

def exact_scan(rows,alpha=.05):
    features=sorted({(str(r["region"]),str(r.get("feature_type","SNV")).upper()) for r in rows})
    cases=_patients(rows,{"case","cancer","tumor"}); controls=_patients(rows,{"control","healthy","normal"})
    if not cases or not controls: return []
    out=[]
    for region,ft in features:
        sub=[r for r in rows if str(r["region"])==region and str(r.get("feature_type","SNV")).upper()==ft]
        cd={r["patient"] for r in sub if r["patient"] in cases and r.get("status")=="Detected"}
        hd={r["patient"] for r in sub if r["patient"] in controls and r.get("status")=="Detected"}
        a,b=len(cd),len(hd); cf=a/len(cases); hf=b/len(controls)
        out.append({"region":region,"feature_type":ft,"case_frequency":cf,"control_frequency":hf,"effect_size":abs(cf-hf),"p_value":fisher_exact_2x2(a,b,len(cases)-a,len(controls)-b)})
    q=benjamini_hochberg([r["p_value"] for r in out])
    for r,v in zip(out,q): r["q_value"]=v; r["significant"]=v<=alpha
    return out

def coarse_to_fine_scan(rows,alpha=.05,effect_threshold=.10,neighbor_k=1):
    exact=exact_scan(rows,alpha); retained=set()
    for size in RESOLUTIONS[:-1]:
        for r in rows:
            for region in _bin(r["region"],size):
                ft=str(r.get("feature_type","SNV")).upper()
                sub=[x for x in rows if str(x.get("feature_type","SNV")).upper()==ft and region in _bin(x["region"],size)]
                cases=_patients(sub,{"case","cancer","tumor"}); controls=_patients(sub,{"control","healthy","normal"})
                if not cases or not controls: continue
                cf=len({x["patient"] for x in sub if x["patient"] in cases and x.get("status")=="Detected"})/len(cases)
                hf=len({x["patient"] for x in sub if x["patient"] in controls and x.get("status")=="Detected"})/len(controls)
                if abs(cf-hf)>=effect_threshold: retained.add((region,ft))
    final=[r for r in exact if r["significant"]]
    return {"resolutions":[LABELS[x] for x in RESOLUTIONS],"exact":exact,"retained_regions":sorted(retained),"final":final,"neighbor_k":neighbor_k}