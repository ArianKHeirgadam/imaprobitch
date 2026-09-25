"""Pipeline orchestration runner."""

from .config import DEFAULT_STAGES
from .stages import run_stage


def execute_pipeline(payload):
    results = []

    current = payload

    for stage in DEFAULT_STAGES:
        result = run_stage(stage, current)
        results.append(result)
        current = result

    return results
