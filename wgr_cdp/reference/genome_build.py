"""Genome build registry for WGR-CDP Phase 3."""

SUPPORTED_BUILDS = {
    "GRCh38": {
        "status": "primary",
        "aliases": ["hg38", "GRCh38.p14"],
    },
    "GRCh37": {
        "status": "legacy",
        "aliases": ["hg19"],
    },
}


def resolve_build(name):
    if name in SUPPORTED_BUILDS:
        return name

    for build, info in SUPPORTED_BUILDS.items():
        if name in info["aliases"]:
            return build

    return None
