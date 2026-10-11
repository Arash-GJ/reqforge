"""HTML report security and CLI integration tests."""

from pathlib import Path

from typer.testing import CliRunner

from reqforge.cli import app
from reqforge.core import Result
from reqforge.reporting import save_report


def test_html_report_escapes_untrusted_values(tmp_path: Path) -> None:
    target = tmp_path / "report.html"
    results = [Result(name="<script>alert(1)</script>", passed=False, status=500, duration_ms=5.5, error="<img src=x onerror=alert(1)>")]
    save_report(results, target, "html")
    html = target.read_text(encoding="utf-8")
    assert "&lt;script&gt;" in html
    assert "&lt;img" in html
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "0/1 passed" in html


def test_html_report_empty_suite(tmp_path: Path) -> None:
    target = tmp_path / "empty.html"
    save_report([], target, "html")
    assert "0/0 passed" in target.read_text(encoding="utf-8")


def test_cli_accepts_html_format() -> None:
    result = CliRunner().invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "html" in result.output
