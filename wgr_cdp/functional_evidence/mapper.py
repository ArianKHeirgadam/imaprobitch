"""Normalize functional evidence from external providers."""


def map_functional_evidence(evidence):
    """Map provider output to the stable WGR-CDP functional schema."""
    evidence = evidence or {}
    return {
        "source": evidence.get("source"),
        "gene": evidence.get("gene"),
        "consequence": evidence.get("consequence"),
        "impact": evidence.get("impact"),
        "transcript": evidence.get("transcript"),
        "protein_change": evidence.get("protein_change"),
        "regulatory_consequence": evidence.get("regulatory_consequence"),
    }
