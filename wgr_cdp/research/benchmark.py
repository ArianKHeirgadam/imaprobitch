"""Fast-vs-exact benchmark with runtime and peak-memory measurements."""
import time, tracemalloc

def benchmark(exact_fn,fast_fn,data):
    def run(fn):
        tracemalloc.start(); t=time.perf_counter(); out=fn(data); elapsed=time.perf_counter()-t; _,peak=tracemalloc.get_traced_memory(); tracemalloc.stop(); return out,elapsed,peak
    exact,te,me=run(exact_fn); fast,tf,mf=run(fast_fn)
    e={str(x.get("region"))+"|"+str(x.get("feature_type")) for x in exact if x.get("significant")}
    f={str(x.get("region"))+"|"+str(x.get("feature_type")) for x in fast.get("final",[]) if x.get("significant")}
    inter=len(e&f)
    return {"exact_runtime_s":te,"fast_runtime_s":tf,"exact_peak_bytes":me,"fast_peak_bytes":mf,"exact_hits":len(e),"fast_hits":len(f),"recall":inter/len(e) if e else 1.0,"precision":inter/len(f) if f else (1.0 if not e else 0.0),"regions_evaluated_fast":len(fast.get("retained_regions",[]))}