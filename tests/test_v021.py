"""Regression tests for the bundled example contract and CLI errors."""

from pathlib import Path

import httpx
from typer.testing import CliRunner

from reqforge.cli import app
from reqforge.contracts import load_contract, validate_response

EXAMPLE_CONTRACT = Path(__file__).resolve().parents[1] / "examples" / "openapi.yaml"


def test_example_contract_covers_get_and_post():
    contract = load_contract(EXAMPLE_CONTRACT)
    assert validate_response(contract, "GET", "https://httpbin.org/get", httpx.Response(200, json={})) == []
    assert validate_response(
        contract,
        "POST",
        "https://httpbin.org/post",
        httpx.Response(200, json={"json": {"project": "ReqForge"}}),
    ) == []


def test_diff_invalid_run_id_exits_without_traceback(tmp_path):
    runner = CliRunner()
    result = runner.invoke(app, ["diff", "RUN_ID_1", "RUN_ID_2", "--db", str(tmp_path / "history.db")])
    assert result.exit_code == 2
    assert "History error" in result.output
    assert "Traceback" not in result.output


def test_send_invalid_json_exits_without_traceback():
    result = CliRunner().invoke(app, ["send", "POST", "https://example.com", "--json", "{"])
    assert result.exit_code == 2
    assert "Request failed" in result.output
    assert "Traceback" not in result.output
