"""Terminal interface for ReqForge."""

import asyncio
import json
from pathlib import Path
from typing import Annotated
import httpx
import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .core import load_suite, run_suite
from .reporting import save_report

app = typer.Typer(
    help="ReqForge: API requests and asynchronous YAML test suites.", no_args_is_help=True
)
console = Console()


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(__version__)


@app.command()
def send(
    method: Annotated[str, typer.Argument(help="HTTP method")],
    url: Annotated[str, typer.Argument(help="Absolute HTTP(S) URL")],
    header: Annotated[
        list[str] | None,
        typer.Option("--header", "-H", help="Header: Name: Value"),
    ] = None,
    body: Annotated[
        str | None,
        typer.Option("--json", help="JSON request body"),
    ] = None,
    timeout: Annotated[
        float,
        typer.Option(min=0.1),
    ] = 15.0,
) -> None:
    """Send one HTTP request and print its response."""
    if not url.startswith(("http://", "https://")):
        raise typer.BadParameter("URL must be HTTP(S)")
    headers = {}
    for item in header or []:
        if ":" not in item:
            raise typer.BadParameter("Headers must be 'Name: Value'")
        name, value = item.split(":", 1)
        headers[name.strip()] = value.strip()
    try:
        payload = json.loads(body) if body is not None else None
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            response = client.request(method.upper(), url, headers=headers, json=payload)
        console.print(
            f"[bold]HTTP {response.status_code}[/bold] ({response.elapsed.total_seconds() * 1000:.0f} ms)"
        )
        try:
            console.print_json(data=response.json())
        except ValueError:
            console.print(response.text[:10000])
        if response.is_error:
            raise typer.Exit(code=1)
    except (httpx.HTTPError, ValueError) as exc:
        console.print(f"[red]Request failed:[/red] {exc}", stderr=True)
        raise typer.Exit(code=2) from exc


@app.command()
def run(
    suite: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    parallel: Annotated[
        int,
        typer.Option(min=1, max=100),
    ] = 5,
    timeout: Annotated[
        float,
        typer.Option(min=0.1),
    ] = 15.0,
    report: Annotated[
        Path | None,
        typer.Option(help="Report output path"),
    ] = None,
    format: Annotated[
        str,
        typer.Option(help="Report format: json or junit"),
    ] = "json",
) -> None:
    """Execute YAML API tests and return a CI-friendly exit code."""
    if format not in ("json", "junit"):
        raise typer.BadParameter("format must be json or junit")
    try:
        cases = load_suite(suite)
        results = asyncio.run(run_suite(cases, parallel=parallel, timeout=timeout))
        if report:
            save_report(results, report, format)
    except (ValueError, OSError) as exc:
        console.print(f"[red]Suite error:[/red] {exc}", stderr=True)
        raise typer.Exit(code=2) from exc
    table = Table("Test", "Status", "HTTP", "Duration", "Details")
    for result in results:
        table.add_row(
            result.name,
            "PASS" if result.passed else "FAIL",
            str(result.status or "-"),
            f"{result.duration_ms:.0f} ms",
            result.error or "",
        )
    console.print(table)
    failed = sum(not result.passed for result in results)
    console.print(f"{len(results) - failed}/{len(results)} passed")
    if failed:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
