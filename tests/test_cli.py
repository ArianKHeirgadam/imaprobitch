import pytest

from wgr_cdp.cli.main import execute


def test_cli_commands():
    assert execute("run")["status"] == "completed"
    assert execute("validate")["command"] == "validate"
    assert execute("release")["command"] == "release"
    assert execute("release")["scientific_results"] == "CONDITIONAL"
    assert execute("report")["command"] == "report"


def test_unknown_cli_command():
    with pytest.raises(ValueError):
        execute("unknown")
