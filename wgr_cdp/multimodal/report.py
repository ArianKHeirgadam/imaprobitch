"""HTML report for multimodal WGR-CDP analysis."""
from pathlib import Path
from html import escape

def write_report(output, result, rows):
    output=Path(output)
    by_type={}
    for r in rows: by_type.setdefault(r["feature_type"],[]).append(r)
    html_rows=[]
    for ft,items in by_type.items():
        for x in items[:50]:
            html_rows.append("<tr>"+"".join("<td>"+escape(str(x.get(k,"")))+"</td>" for k in ["region","feature_type","value","status","stage","tumor_fraction","depth","blood_background","validation_status"])+"</tr>")
    html_doc=(
        "<html><head><meta charset='utf-8'><title>WGR-CDP multimodal report</title>"
        "<style>body{font-family:Arial;margin:30px}table{border-collapse:collapse;width:100%}"
        "td,th{border:1px solid #ccc;padding:5px}</style></head><body>"
        "<h1>WGR-CDP Multimodal Research Report</h1>"
        "<p>Feature types: "+escape(", ".join(result["feature_types"]))+"</p>"
        "<p>Patients covered by selected panel: "+str(result["panel"]["covered_patients"])+"/"+str(result["panel"]["patient_count"])+"</p>"
        "<p>Estimated LoD: "+str(result["lod"])+"</p>"
        "<h2>Input features</h2><table><tr><th>Region</th><th>Type</th><th>Value</th><th>Status</th><th>Stage</th><th>Tumor fraction</th><th>Depth</th><th>Blood background</th><th>Validation</th></tr>"
        + "".join(html_rows) + "</table>"
        "<p><strong>Research use only.</strong> Detectability/LoD outputs are computational estimates and require assay-specific validation.</p>"
        "</body></html>"
    )
    (output/"report.html").write_text(html_doc,encoding="utf-8")
