"""Small dependency-free ClinVar E-utilities client.

The client uses NCBI E-utilities for read-only ClinVar lookups. Network access is
kept behind an injectable request function so tests remain deterministic.
"""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from wgr_cdp.annotation_integration.mapper import map_annotation


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class ClinVarClient:
    """Read-only ClinVar lookup client."""

    def __init__(self, request_get=None, timeout=10):
        self.request_get = request_get or self._default_request_get
        self.timeout = timeout

    def lookup_variant(self, variant):
        """Look up one variant using ClinVar's coordinate-style search."""
        term = self._variant_term(variant)
        search = self._request_json(
            "/esearch.fcgi",
            {"db": "clinvar", "term": term, "retmode": "json", "retmax": "1"},
        )
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return map_annotation({"source": "clinvar"})

        summary = self._request_json(
            "/esummary.fcgi",
            {"db": "clinvar", "id": ids[0], "retmode": "json"},
        )
        return self._map_summary(summary, ids[0])

    def _variant_term(self, variant):
        chrom = str(variant["chrom"]).removeprefix("chr")
        return f"{chrom}-{variant['pos']}-{variant['ref']}-{variant['alt']}"

    def _request_json(self, path, params):
        url = f"{EUTILS_BASE}{path}?{urlencode(params)}"
        payload = self.request_get(url, self.timeout)
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return json.loads(payload)

    @staticmethod
    def _default_request_get(url, timeout):
        request = Request(
            url,
            headers={"User-Agent": "WGR-CDP/1.0 (research; contact-required)"},
        )
        with urlopen(request, timeout=timeout) as response:
            return response.read()

    @staticmethod
    def _map_summary(summary, variation_id):
        result = summary.get("result", {})
        record = result.get(str(variation_id), {})
        gene = record.get("gene_symbol") or record.get("gene")
        consequence = record.get("variant_type")
        clinical_significance = (
            record.get("clinical_significance")
            or record.get("clinical_significance_description")
        )
        mapped = map_annotation({
            "gene": gene,
            "consequence": consequence,
            "impact": clinical_significance,
            "source": "clinvar",
        })
        mapped["clinvar_id"] = variation_id
        mapped["clinvar_accession"] = record.get("accession")
        mapped["clinical_significance"] = clinical_significance
        mapped["clinical_significance_raw"] = record.get("clinical_significance")
        return mapped
