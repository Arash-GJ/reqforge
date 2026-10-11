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
- [ ] OpenAPI contract validation
- [ ] Run history and regression diff
- [ ] Plugin hooks
- [ ] HTML reports

## License

MIT
