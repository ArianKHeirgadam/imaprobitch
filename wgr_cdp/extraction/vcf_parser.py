from pathlib import Path
from .schema import FeatureObservation

def _kind(ref,alt,info):
    if alt.startswith("<") or "SVTYPE=" in info: return "SV"
    return "SNV" if len(ref)==1 and len(alt)==1 else "INDEL"

def parse_vcf(path):
    path=Path(path); out=[]; samples=[]
    with path.open(encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.startswith("#CHROM"): samples=line.rstrip().split("\t")[9:]; continue
            if line.startswith("#") or not line.strip(): continue
            x=line.rstrip().split("\t")
            if len(x)<8: raise ValueError(f"VCF line {n}: fewer than 8 columns")
            chrom,pos,_,ref,alts,_,filt,info=x[:8]
            if filt not in {"PASS","."}: continue
            fmt=x[8].split(":") if len(x)>8 else []
            for i,s in enumerate(x[9:]):
                sid=samples[i] if i<len(samples) else f"sample_{i+1}"; d=dict(zip(fmt,s.split(":"))); gt=d.get("GT","")
                if gt in {"","./.",".|."} or all(a in {"0","."} for a in gt.replace("|","/").split("/")): continue
                vaf=None
                if d.get("VAF") not in {None,"","."}: vaf=float(d["VAF"])
                elif d.get("AD") not in {None,"","."}:
                    ad=[int(a) for a in d["AD"].split(",") if a!="."]; vaf=sum(ad[1:])/sum(ad) if len(ad)>1 and sum(ad)>0 else None
                depth=float(d["DP"]) if d.get("DP") not in {None,"","."} else None
                for alt in alts.split(","): out.append(FeatureObservation(f"{chrom}:{pos}:{ref}>{alt}",sid,_kind(ref,alt,info),1.0,"Detected",str(path),depth,vaf))
    return out
