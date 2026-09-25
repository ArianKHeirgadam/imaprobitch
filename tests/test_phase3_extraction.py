import textwrap
from wgr_cdp.extraction.vcf_parser import parse_vcf
from wgr_cdp.extraction.cnv_analyzer import parse_cnv_table
from wgr_cdp.extraction.methylation_loader import parse_methylation_table
from wgr_cdp.extraction.mito_analyzer import parse_mito_table

def test_vcf_snv_indel(tmp_path):
    p=tmp_path/"x.vcf"
    p.write_text("##fileformat=VCFv4.3\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tP1\n1\t100\t.\tA\tT\t.\tPASS\t.\tGT:DP:AD\t0/1:30:20,10\n1\t200\t.\tA\tAT\t.\tPASS\t.\tGT\t1/1\n")
    o=parse_vcf(p)
    assert [x.feature_type for x in o]==["SNV","INDEL"]
    assert o[0].vaf==10/30

def test_cnv_missing_is_unavailable(tmp_path):
    p=tmp_path/"x.tsv"; p.write_text("sample_id\tchromosome\tstart\tend\tcopy_number\nP1\t1\t1\t100\t.\n")
    assert parse_cnv_table(p)[0].status=="Data unavailable"

def test_methylation(tmp_path):
    p=tmp_path/"x.tsv"; p.write_text("sample_id\tregion\tbeta\tm_value\nP1\t1:100\t0.8\t1.99\n")
    assert parse_methylation_table(p)[0].beta==0.8

def test_mito(tmp_path):
    p=tmp_path/"x.tsv"; p.write_text("sample_id\tposition\theteroplasmy\tcopy_number\nP1\t100\t0.25\t500\n")
    assert parse_mito_table(p)[0].heteroplasmy==0.25