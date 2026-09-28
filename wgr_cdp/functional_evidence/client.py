"""Small dependency-free Ensembl VEP REST client.

Network access is injectable so tests remain deterministic.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

VEP_BASE = "https://rest.ensembl.org"


class VepClient:
    """Read-only client for Ensembl VEP variant consequence annotations."""

    def __init__(self, request_get=None, timeout=15, species="human"):
        self.request_get = request_get or self._default_request_get
        self.timeout = timeout
        self.species = species

    def annotate_variant(self, variant):
        """Annotate one normalized VCF-style variant with VEP."""
        region = (
            f"{self._chrom(variant['chrom'])}:"
            f"{variant['pos']}-{variant['pos']}"
        )
        allele = f"{variant['ref']}/{variant['alt']}"
        path = (
            f"/vep/{quote(self.species, safe='')}/region/"
            f"{quote(region, safe='')}/{quote(allele, safe='')}"
        )
        records = self._request_json(path)
        if not records:
            return self._empty()

        return self._map_record(records[0])

    def _request_json(self, path):
        url = f"{VEP_BASE}{path}"
        payload = self.request_get(url, self.timeout)
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return json.loads(payload)

    @staticmethod
    def _default_request_get(url, timeout):
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "WGR-CDP/1.0 (research; contact-required)",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            return response.read()

    @staticmethod
    def _chrom(chrom):
        return str(chrom).removeprefix("chr")

    @staticmethod
    def _empty():
        return {
            "source": "ensembl_vep",
            "gene": None,
            "consequence": None,
            "impact": None,
            "transcript": None,
            "protein_change": None,
            "regulatory_consequence": None,
        }

    @staticmethod
    def _map_record(record):
        transcript = record.get("transcript_consequences") or []
        selected = transcript[0] if transcript else {}

        consequences = selected.get("consequence_terms") or []
        protein_change = (
            selected.get("amino_acids")
            or selected.get("protein_start")
            or None
        )

        regulatory = record.get("regulatory_feature_consequences") or []
        regulatory_terms = []
        for item in regulatory:
            regulatory_terms.extend(item.get("consequence_terms") or [])

        return {
            "source": "ensembl_vep",
            "gene": selected.get("gene_symbol") or selected.get("gene_id"),
            "consequence": consequences[0] if consequences else None,
            "impact": selected.get("impact"),
            "transcript": selected.get("transcript_id"),
            "protein_change": protein_change,
            "regulatory_consequence": (
                regulatory_terms[0] if regulatory_terms else None
            ),
        }
