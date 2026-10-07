from pathlib import Path
from wgr_cdp.research.cnv_detection import compare_cnv_events_and_dosage, validate_cnv_cohort

def _rows():
    return [
        {"sample_id":"T1","group":"tumor","chrom":"8","start":100,"end":200,"copy_number":"4","log2_ratio":"1.0","event_type":"GAIN"},
        {"sample_id":"T2","group":"tumor","chrom":"8","start":100,"end":200,"copy_number":"4","log2_ratio":"0.8","event_type":"GAIN"},
        {"sample_id":"N1","group":"comparator","chrom":"8","start":100,"end":200,"copy_number":"2","log2_ratio":"0.0","event_type":"NEUTRAL"},
        {"sample_id":"N2","group":"comparator","chrom":"8","start":100,"end":200,"copy_number":"2","log2_ratio":"0.0","event_type":"NEUTRAL"},
    ]

def test_event_and_dosage_contracts_are_separate():
    result=compare_cnv_events_and_dosage(_rows(), permutations=99, seed=42)
    assert result["case_sample_count"]==2
    assert result["comparator_sample_count"]==2
    assert len(result["event_rows"])==2
    assert len(result["dosage_rows"])==1
    assert all(r["statistical_method"].startswith("Fisher") for r in result["event_rows"])
    assert result["dosage_rows"][0]["statistical_method"]=="permutation_test_mean_difference"

def test_missing_region_is_not_zero_or_negative():
    result=compare_cnv_events_and_dosage(_rows()+[
        {"sample_id":"T3","group":"tumor","chrom":"9","start":500,"end":600,"copy_number":"4","log2_ratio":"1.0","event_type":"GAIN"}],
        permutations=19, seed=42)
    region=next(r for r in result["event_rows"] if r["region"]=="9:500-600")
    assert region["case_n"]==1
    assert region["comparator_n"]==0

def test_validation_writes_provenance_and_contract(tmp_path):
    source=tmp_path/"cnv.csv"
    source.write_text("sample_id,chromosome,start,end,copy_number,log2_ratio,group\nT1,8,100,200,4,1.0,tumor\nT2,8,100,200,4,0.8,tumor\nN1,8,100,200,2,0.0,comparator\nN2,8,100,200,2,0.0,comparator\n",encoding="utf-8")
    result=validate_cnv_cohort(source,tmp_path/"out",permutations=19)
    assert result["status"]=="PASS"
    assert result["event_vs_dosage_contract"]=="SEPARATE"
    assert len(result["source_provenance"])==1
    assert (tmp_path/"out"/"cnv_event_statistics.csv").exists()
    assert (tmp_path/"out"/"cnv_dosage_statistics.csv").exists()

def test_no_comparator_is_conditional(tmp_path):
    source=tmp_path/"cnv.csv"
    source.write_text("sample_id,chromosome,start,end,copy_number,log2_ratio,group\nT1,8,100,200,4,1.0,tumor\n",encoding="utf-8")
    result=validate_cnv_cohort(source,tmp_path/"out")
    assert result["status"]=="CONDITIONAL"
    assert result["comparison_status"]=="Data unavailable"
