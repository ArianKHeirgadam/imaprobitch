"""Fair baseline helpers."""
from math import exp

def top_k(features,k=15):
    return sorted(features,key=lambda r:(-float(r.get("score",r.get("effect_size",0))),str(r.get("feature",r.get("region","")))))[:k]

def logistic_score(x,weights=None,intercept=0):
    weights=weights or [1.0]*len(x); z=float(intercept)+sum(float(a)*float(b) for a,b in zip(x,weights)); z=max(-60,min(60,z)); return 1/(1+exp(-z))

def elastic_net_coordinate_descent(X,y,alpha=1.0,l1_ratio=.5,steps=200,lr=.01):
    if not X: return {"coef":[],"intercept":0.0}
    p=len(X[0]); w=[0.0]*p; b=sum(y)/len(y)
    for _ in range(steps):
        pred=[logistic_score(row,w,b) for row in X]; b-=lr*sum(a-t for a,t in zip(pred,y))/len(y)
        for j in range(p):
            grad=sum((pred[i]-y[i])*X[i][j] for i in range(len(X)))/len(X)+alpha*(1-l1_ratio)*w[j]
            z=w[j]-lr*grad; shrink=max(0,abs(z)-lr*alpha*l1_ratio); w[j]=(1 if z>=0 else -1)*shrink
    return {"coef":w,"intercept":b,"alpha":alpha,"l1_ratio":l1_ratio}