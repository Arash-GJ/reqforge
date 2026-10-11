import httpx
import pytest
from reqforge.core import Case, load_suite, run_suite, nested_value
from reqforge.reporting import save_report


def test_nested_value():
    assert nested_value({"users": [{"id": 7}]}, "users.0.id") == 7


def test_load_suite(tmp_path):
    path = tmp_path / "suite.yaml"
    path.write_text("tests:\n  - name: ok\n    url: https://example.com\n")
    cases = load_suite(path)
    assert len(cases) == 1
    assert cases[0].expected_status == 200


def test_reject_bad_suite(tmp_path):
    path = tmp_path / "suite.yaml"
    path.write_text("tests:\n  - url: file:///etc/passwd\n")
    with pytest.raises(ValueError):
        load_suite(path)


@pytest.mark.asyncio
async def test_run_suite_success_and_failure():
    def handler(request):
        return httpx.Response(200, json={"data": {"id": 3}}, headers={"x-service": "demo"})
    transport = httpx.MockTransport(handler)
    cases = [
        Case("pass", "GET", "https://example.com", expected_json={"data.id": 3}, expected_headers={"x-service": "demo"}),
        Case("fail", "GET", "https://example.com", expected_status=404),
    ]
    results = await run_suite(cases, transport=transport)
    assert [r.passed for r in results] == [True, False]
    assert "Expected HTTP 404" in results[1].error


def test_reports(tmp_path):
    from reqforge.core import Result
    results = [Result("ok", True, 200, 12), Result("bad", False, 500, 13, "oops")]
    save_report(results, tmp_path / "results.json", "json")
    save_report(results, tmp_path / "results.xml", "junit")
    assert '"passed": true' in (tmp_path / "results.json").read_text()
    assert 'failures="1"' in (tmp_path / "results.xml").read_text()
