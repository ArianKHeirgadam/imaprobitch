"""Pipeline run tracking utilities."""

import uuid
from datetime import datetime, timezone


def create_run_id():
    """
    Generate a unique identifier for a pipeline execution run.
    """
    return str(uuid.uuid4())


def create_run_record(config=None):
    """
    Create a reproducible pipeline execution record.

    Args:
        config (dict | None): Pipeline configuration snapshot.

    Returns:
        dict: Run metadata record.
    """
    return {
        "run_id": create_run_id(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config or {},
    }