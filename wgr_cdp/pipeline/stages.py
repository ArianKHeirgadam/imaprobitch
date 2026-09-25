"""Pipeline stage interfaces."""


def run_stage(name, payload):
    return {
        "stage": name,
        "status": "completed",
        "payload": payload,
    }
