# ReqForge ⚡

**Async API testing from your terminal.** ReqForge is an open-source Python CLI for running YAML-defined HTTP tests, checking API responses against OpenAPI contracts, tracking execution history, and generating CI-friendly reports.

[![CI](https://github.com/Arash-GJ/reqforge/actions/workflows/ci.yml/badge.svg)](https://github.com/Arash-GJ/reqforge/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Arash-GJ/reqforge)](https://github.com/Arash-GJ/reqforge/releases/tag/v0.3.0)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

**[Latest release: v0.3.0](https://github.com/Arash-GJ/reqforge/releases/tag/v0.3.0)** · [CI results](https://github.com/Arash-GJ/reqforge/actions) · [Source code](https://github.com/Arash-GJ/reqforge)

## Features

- **Async execution:** run HTTP API tests concurrently with configurable parallelism.
- **YAML suites:** define requests, expected status codes, response headers, and JSON assertions.
- **OpenAPI validation:** opt-in checks for supported OpenAPI 3.x response contracts.
- **Execution history:** persist run results locally in SQLite.
- **Regression comparison:** compare two runs to find new failures and fixes.
- **Reports:** export JSON, JUnit XML, or self-contained HTML reports.
- **Quality checks:** automated Pytest and Ruff checks in GitHub Actions for Python 3.11, 3.12, and 3.13.

## Quick start

Requires Python 3.11 or newer.

```bash
git clone https://github.com/Arash-GJ/reqforge.git
cd reqforge
python -m venv .venv
# Activate the virtual environment, then:
python -m pip install -e ".[dev]"
reqforge --help
```

Windows CMD activation: `.venv\Scripts\activate.bat`  
macOS/Linux activation: `source .venv/bin/activate`

## Run an API test suite

```bash
reqforge run examples/api.yaml
reqforge run examples/api.yaml --parallel 5
reqforge run examples/api.yaml --contract examples/openapi.yaml
```

Example YAML suite:

```yaml
tests:
  - name: HTTPBin GET
    method: GET
    url: https://httpbin.org/get
    expect_status: 200
  - name: HTTPBin POST
    method: POST
    url: https://httpbin.org/post
    json:
      project: ReqForge
    expect_status: 200
    expect_json:
      json.project: ReqForge
```

The bundled example calls the public HTTPBin service and therefore needs an internet connection.

## Reports

Generate an offline HTML report:

```bash
reqforge run examples/api.yaml --contract examples/openapi.yaml --report reports/latest.html --format html
```

Open `reports/latest.html` in a browser. The report shows per-test status, HTTP status, duration, and error details; untrusted test names and errors are HTML-escaped.

For machine-readable output:

```bash
reqforge run examples/api.yaml --report reports/results.json
reqforge run examples/api.yaml --format junit --report reports/junit.xml
```

## Run history and regression detection

```bash
reqforge history
reqforge diff FIRST_REAL_RUN_ID SECOND_REAL_RUN_ID
```

Replace the placeholders with run IDs shown by `reqforge history`. Run history is stored in SQLite at `~/.reqforge/history.sqlite3` by default. You can choose a different database with `--history-db`.

## Development

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m pytest -v
```

CI runs these checks across Python 3.11, 3.12, and 3.13.

## Current limitations

OpenAPI checks currently focus on literal paths, declared response statuses, JSON bodies, and a common OpenAPI 3.1 JSON Schema subset. Templated paths, remote `$ref`, OpenAPI 3.0-specific `nullable`/`discriminator`, and other advanced OpenAPI semantics are not yet supported. External references are not fetched.

**Security:** Only run trusted YAML suites. Suites can send requests to arbitrary URLs; never commit credentials or sensitive response data. Reports and history may contain error details. Redirects are disabled.

## Roadmap

- [x] Async YAML-based test runner
- [x] JSON and JUnit reporting
- [x] OpenAPI response checks
- [x] SQLite run history and regression diff
- [x] HTML reports
- [ ] Plugin hooks
- [ ] Additional OpenAPI features

## License

MIT.
