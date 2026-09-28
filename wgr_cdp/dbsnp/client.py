"""Dependency-free NCBI Variation Services client for dbSNP.

The network layer is injectable so tests are deterministic and do not require
internet access.
"""

import json
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE_URL = "https://api.ncbi.nlm.nih.gov/variation/v0"


class DbSnpClient:
    """Resolve normalized VCF variants to dbSNP RefSNP records."""

    def __init__(self, request_get=None, timeout=10):
        self.request_get = request_get or self._default_request_get
        self.timeout = timeout

    def lookup_variant(self, variant):
        """Return a stable dbSNP annotation for one VCF-style variant."""
        contextuals = self._request_json(
            f"/vcf/{self._path(variant['chrom'])}/{variant['pos']}/"
            f"{self._path(variant['ref'])}/{self._path(variant['alt'])}/contextuals"
        )
        spdis = contextuals.get("data", {}).get("spdis", [])
        if not spdis:
            return self._empty_result()

        rsids = []
        for spdi in spdis:
            value = self._spdi_string(spdi)
            response = self._request_json(
                f"/spdi/{quote(value, safe=':')}/rsids"
            )
            rsids.extend(response.get("data", {}).get("rsids", []))

        rsids = self._unique(rsids)
        result = self._empty_result()
        result["dbsnp_rsids"] = [f"rs{rsid}" for rsid in rsids]

        if rsids:
            record = self._request_json(f"/refsnp/{rsids[0]}")
            result.update(self._map_refsnp(record, rsids[0]))

        return result

    def _request_json(self, path):
        payload = self.request_get(f"{BASE_URL}{path}", self.timeout)
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
    def _path(value):
        return quote(str(value), safe="")

    @staticmethod
    def _spdi_string(spdi):
        return ":".join(
            [
                str(spdi["seq_id"]),
                str(spdi["position"]),
                str(spdi["deleted_sequence"]),
                str(spdi["inserted_sequence"]),
            ]
        )

    @staticmethod
    def _unique(values):
        return list(dict.fromkeys(str(value) for value in values))

    @staticmethod
    def _empty_result():
        return {
            "gene": None,
            "consequence": None,
            "impact": None,
            "source": "dbsnp",
            "dbsnp_rsids": [],
            "dbsnp_variant_type": None,
        }

    @staticmethod
    def _map_refsnp(record, rsid):
        snapshot = record.get("primary_snapshot_data", {})
        return {
            "dbsnp_variant_type": snapshot.get("variant_type"),
            "dbsnp_ref_snp_id": f"rs{rsid}",
        }
