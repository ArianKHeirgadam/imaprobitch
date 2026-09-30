"""Dependency-light statistics for the WGR-CDP scientific completion layer."""
from math import comb, asin, sqrt

def benjamini_hochberg(p_values):
    values=[float(p) for p in p_values]
    if any(p<0 or p>1 for p in values): raise ValueError("p-values must be between 0 and 1")
    n=len(values); ranked=sorted(enumerate(values), key=lambda x:(x[1],x[0]))
    out=[1.0]*n; running=1.0
    for rank in range(n,0,-1):
        idx,p=ranked[rank-1]; running=min(running,p*n/rank); out[idx]=min(1.0,running)
    return out

def fisher_exact_2x2(a,b,c,d):
    a,b,c,d=map(int,(a,b,c,d))
    if min(a,b,c,d)<0: raise ValueError("2x2 counts must be non-negative")
    r1,r2,col1,total=a+b,c+d,a+c,a+b+c+d
    if total==0: return 1.0
    den=comb(total,col1)
    def prob(x):
        if x<0 or x>r1 or col1-x<0 or col1-x>r2: return 0.0
        return comb(r1,x)*comb(r2,col1-x)/den
    obs=prob(a); lo,hi=max(0,col1-r2),min(r1,col1)
    return min(1.0,sum(prob(x) for x in range(lo,hi+1) if prob(x)<=obs+1e-15))

def cohen_h(p1,p2):
    p1=max(0,min(1,float(p1))); p2=max(0,min(1,float(p2)))
    return 2*abs(asin(sqrt(p1))-asin(sqrt(p2)))

def per_feature_alpha(fpr_target,k):
    fpr_target,k=float(fpr_target),int(k)
    if not 0<fpr_target<1 or k<1: raise ValueError("fpr_target must be in (0,1) and k >= 1")
    return 1-(1-fpr_target)**(1/k)