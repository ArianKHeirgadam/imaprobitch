"""Execution history storage interface."""


def append_history(history, run_record):
    history.append(run_record)
    return history
