"""Pipeline execution errors."""


class PipelineExecutionError(RuntimeError):
    """Raised when a pipeline stage fails in fail-fast mode."""

    def __init__(self, stage, cause):
        self.stage = stage
        self.cause = cause
        super().__init__(f"pipeline stage '{stage}' failed: {cause}")
