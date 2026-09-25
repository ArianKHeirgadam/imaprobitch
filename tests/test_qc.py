from wgr_cdp.qc.harmonization import normalize_chromosome, normalize_sample_id

def test_chr_normalization():
    assert normalize_chromosome('chr1') == '1'

def test_sample_normalization():
    assert normalize_sample_id('sample A') == 'sample_A'
