from wgr_cdp.data_ingestion.cnv import classify_event, read_cnv_segments
from wgr_cdp.cnv_analysis.analysis import analyze_cnv_segments

def test_cnv_classification_from_copy_number():
    assert classify_event(copy_number=3) == "GAIN"
    assert classify_event(copy_number=1) == "LOSS"
    assert classify_event(copy_number=2) == "NEUTRAL"

def test_cnv_parser_normalizes_chromosome_and_group(tmp_path):
    path = tmp_path/"cnv.csv"
    path.write_text("sample_id,chromosome,start,end,log2_ratio,genes\nC1,chr8,100,200,0.8,GENE1;GENE2\n", encoding="utf-8")
    rows = read_cnv_segments(path, group="case")
    assert rows[0]["chrom"] == "8"
    assert rows[0]["event_type"] == "GAIN"
    assert rows[0]["status"] == "Detected"
    assert rows[0]["group"] == "case"

def test_cnv_real_cohort_analysis(tmp_path):
    path = tmp_path/"cnv.csv"
    path.write_text("sample_id,chromosome,start,end,copy_number,genes,group\nC1,8,100,200,4,GENE1,case\nC2,8,100,200,4,GENE1,case\nH1,8,100,200,2,GENE1,control\nH2,8,100,200,2,GENE1,control\n", encoding="utf-8")
    rows = read_cnv_segments(path)
    result = analyze_cnv_segments(rows, tmp_path/"out")
    assert result["regions_tested"] == 1
    assert result["significant_cnvs"] == 1
    assert (tmp_path/"out"/"cnv_segments.csv").exists()
    assert (tmp_path/"out"/"cnv_candidates.csv").exists()
