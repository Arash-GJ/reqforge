# ReqForge ⚡

**Async API testing from your terminal.** A Python CLI for sending HTTP requests, running YAML test suites, asserting JSON fields and HTTP headers, and exporting CI-friendly reports.

> Status: v0.1.0 MVP. Contract validation, history/diff, plugins and HTML reports are **planned**, not implemented.

## Requirements

Python 3.11+

## Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
```

## Commands

```bash
reqforge --help
reqforge version
reqforge send GET https://httpbin.org/get
reqforge send POST https://httpbin.org/post --json '{"hello":"world"}' -H 'X-Demo: yes'
reqforge run examples/api.yaml --parallel 5 --report reports/results.json
reqforge run examples/api.yaml --format junit --report reports/junit.xml
```

Suite format:

```yaml
tests:
  - name: user endpoint
    method: GET
    url: https://httpbin.org/json
    expect_status: 200
    expect_headers:
      content-type: application/json
```

`expect_json` maps dotted paths (including numeric list indices) to exact expected values. Tests are executed concurrently with a configurable semaphore. Failed assertions or HTTP errors cause exit code 1. Invalid configuration and transport errors in `send` cause exit code 2.

**Security:** Suites can send requests to arbitrary URLs. Only run trusted suite files; never run untrusted suites inside privileged networks. Redirects are disabled. Avoid placing credentials in committed YAML or command arguments. Responses may contain sensitive data, so treat logs/reports accordingly.

## Development

```bash
ruff check .
pytest -q
```

## Roadmap

- [x] Async test runner
- [x] YAML test definitions
- [x] HTTP and JSON assertions
- [x] JSON / JUnit reports
- [x] CI tests
- [x] OpenAPI contract validation
- [x] Run history and regression diff
- [ ] Plugin hooks
- [ ] HTML reports

## License

MIT

## v0.2.0 — OpenAPI checks and execution history

This release adds **opt-in OpenAPI 3.x response validation**, persistent local run history,
and deterministic pass/fail regression comparison. Install with `pip install -e '.[dev]'`.

```bash
reqforge run examples/api.yaml --contract examples/openapi.yaml
reqforge history
reqforge diff OLD_RUN_ID NEW_RUN_ID
reqforge run examples/api.yaml --history-db ./local-history.sqlite3
```

A run ID is printed and stored in `~/.reqforge/history.sqlite3` (or `--history-db`).
`diff` exits with code 1 for new failing tests, code 2 for invalid run IDs, and 0 otherwise.
Existing `--report` JSON/JUnit output remains supported.

**Current contract validation scope:** literal OpenAPI paths, declared HTTP response statuses,
`application/json` bodies and JSON Schema validation for the common OpenAPI 3.1 subset.
OpenAPI 3.0-specific `nullable`/`discriminator`, templated paths, remote `$ref`, and advanced
OpenAPI semantics are **not yet supported**. External references are never fetched.
Do not store secrets in test names or responses; reports and history may contain error details.

## v0.2.1 — Example contract and CLI error handling fixes

- The bundled OpenAPI example now declares both `GET /get` and `POST /post`, matching `examples/api.yaml`.
- Error messages use a dedicated Rich stderr console instead of an unsupported `stderr` argument.
- `reqforge diff` requires two **real** run IDs from `reqforge history`; names such as `OLD_RUN_ID` are placeholders.
- On Windows Command Prompt, do not paste lines starting with `#` (they are not CMD comments).

```cmd
reqforge run examples/api.yaml --contract examples/openapi.yaml
reqforge history
reqforge run examples/api.yaml --contract examples/openapi.yaml
reqforge history
reqforge diff FIRST_REAL_RUN_ID SECOND_REAL_RUN_ID
```

## HTML report (v0.3.0)

```cmd
reqforge run examples/api.yaml --contract examples/openapi.yaml --report reports/latest.html --format html
```

Open `reports/latest.html` in a browser. The report is self-contained, offline, and HTML-escapes untrusted test names and errors. JSON and JUnit reports remain supported.
