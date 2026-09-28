from wgr_cdp.data_ingestion.cnv import read_cnv_segments
from wgr_cdp.cnv_analysis.analysis import analyze_cnv_segments


def test_cnv_real_cohort_analysis(tmp_path):

    path = tmp_path / "cnv.csv"

    rows_text = (
        "sample_id,chromosome,start,end,copy_number,genes,group\n"
    )

    for i in range(1, 11):
        rows_text += (
            f"C{i},8,100,200,4,GENE1,case\n"
        )

    for i in range(1, 11):
        rows_text += (
            f"H{i},8,100,200,2,GENE1,control\n"
        )

    path.write_text(
        rows_text,
        encoding="utf-8"
    )


    rows = read_cnv_segments(path)


    assert len(rows) == 20

    assert rows[0]["group"] == "case"

    assert rows[0]["event_type"] == "GAIN"


    result = analyze_cnv_segments(
        rows,
        tmp_path / "results"
    )


    assert result["regions_tested"] == 1

    assert result["significant_cnvs"] == 1



def test_cnv_classification():

    rows = [
        {
            "sample_id": "C1",
            "group": "case",
            "chrom": "8",
            "start": 100,
            "end": 200,
            "copy_number": "4",
            "genes": "GENE1",
        }
    ]

    assert rows[0]["copy_number"] == "4"



def test_cnv_requires_groups(tmp_path):

    path = tmp_path / "only_case.csv"

    path.write_text(
        "sample_id,chromosome,start,end,copy_number,genes,group\n"
        "C1,8,100,200,4,GENE1,case\n",
        encoding="utf-8"
    )


    rows = read_cnv_segments(path)

    assert rows[0]["group"] == "case"