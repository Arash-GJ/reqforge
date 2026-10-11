"""Suite parsing and API assertions. No CLI dependencies."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import yaml


@dataclass
class Case:
    name: str
    method: str
    url: str
    expected_status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    json_body: Any = None
    expected_json: dict[str, Any] = field(default_factory=dict)
    expected_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class Result:
    name: str
    passed: bool
    status: int | None
    duration_ms: float
    error: str | None = None


def load_suite(path: Path) -> list[Case]:
    """Parse an explicitly trusted local suite. Never interpolate or execute YAML."""
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict) or not isinstance(content.get("tests"), list):
        raise TypeError("Suite must contain a 'tests' list")
    cases = []
    for index, raw in enumerate(content["tests"], 1):
        if not isinstance(raw, dict):
            raise TypeError(f"Test #{index} must be a mapping")
        try:
            url = raw["url"]
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise ValueError("url must start with http:// or https://")
            method = str(raw.get("method", "GET")).upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
                raise ValueError(f"unsupported method: {method}")
            expected_json = raw.get("expect_json", {})
            expected_headers = raw.get("expect_headers", {})
            headers = raw.get("headers", {})
            if not all(isinstance(x, dict) for x in (expected_json, expected_headers, headers)):
                raise TypeError("headers, expect_headers and expect_json must be mappings")
            cases.append(Case(
                name=str(raw.get("name", f"test-{index}")), method=method, url=url,
                expected_status=int(raw.get("expect_status", 200)), headers=headers,
                json_body=raw.get("json"), expected_json=expected_json,
                expected_headers=expected_headers,
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid test #{index}: {exc}") from exc
    return cases


def nested_value(data: Any, dotted_path: str) -> Any:
    current = data
    for part in dotted_path.split("."):
        if isinstance(current, dict):
            current = current[part]
        elif isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        else:
            raise KeyError(dotted_path)
    return current


async def execute_case(case: Case, client: httpx.AsyncClient, contract: dict | None = None) -> Result:
    import time
    started = time.perf_counter()
    status = None
    try:
        response = await client.request(
            case.method, case.url, headers=case.headers, json=case.json_body
        )
        status = response.status_code
        if contract is not None:
            from .contracts import validate_response
            violations = validate_response(contract, case.method, case.url, response)
            if violations:
                raise AssertionError("OpenAPI: " + "; ".join(violations))
        if status != case.expected_status:
            raise AssertionError(f"Expected HTTP {case.expected_status}, got {status}")
        for header, expected in case.expected_headers.items():
            actual = response.headers.get(header)
            if actual != expected:
                raise AssertionError(f"Header {header!r}: expected {expected!r}, got {actual!r}")
        if case.expected_json:
            data = response.json()
            for path, expected in case.expected_json.items():
                try:
                    actual = nested_value(data, str(path))
                except (KeyError, IndexError, TypeError) as exc:
                    raise AssertionError(f"JSON path {path!r} not found") from exc
                if actual != expected:
                    raise AssertionError(f"JSON {path!r}: expected {expected!r}, got {actual!r}")
        return Result(case.name, True, status, (time.perf_counter() - started) * 1000)
    except (httpx.HTTPError, AssertionError, ValueError) as exc:
        return Result(case.name, False, status, (time.perf_counter() - started) * 1000, str(exc))


async def run_suite(
    cases: list[Case], parallel: int = 5, timeout: float = 15,
    transport: httpx.AsyncBaseTransport | None = None,
    contract: dict | None = None,
) -> list[Result]:
    if parallel < 1 or timeout <= 0:
        raise ValueError("parallel and timeout must be positive")
    semaphore = asyncio.Semaphore(parallel)
    async with httpx.AsyncClient(timeout=timeout, transport=transport, follow_redirects=False) as client:
        async def limited(case: Case) -> Result:
            async with semaphore:
                return await execute_case(case, client, contract)
        return await asyncio.gather(*(limited(case) for case in cases))
