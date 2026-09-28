"""WGR-CDP command line interface."""

from .commands import report_command, run_command, validate_command


def execute(command):
    commands = {
        "run": run_command,
        "validate": validate_command,
        "report": report_command,
    }
    if command not in commands:
        raise ValueError(f"Unknown command: {command}")
    return commands[command]()
