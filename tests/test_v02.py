import httpx
import pytest

from reqforge.contracts import load_contract, validate_response
from reqforge.core import Case, Result, run_suite
from reqforge.history import compare_runs, get_run, list_runs, save_run


def test_history_round_trip(tmp_path):
    db = tmp_path / 'history.sqlite3'
    original = [Result('health', True, 200, 12.5)]
    run_id = save_run(original, db)
    assert get_run(run_id, db) == original
    assert list_runs(db)[0][0] == run_id
    with pytest.raises(ValueError, match='Unknown run'):
        get_run('missing', db)


def test_diff_regressions():
    before = [Result('ok', True, 200, 10), Result('bad', False, 500, 10)]
    after = [Result('ok', False, 500, 10), Result('bad', True, 200, 10)]
    changes = compare_runs(before, after)
    assert changes['regressions'] == ['ok']
    assert changes['fixes'] == ['bad']
    with pytest.raises(ValueError, match='Duplicate'):
        compare_runs(before + before[:1], after)


def test_contract_schema_and_status(tmp_path):
    path = tmp_path / 'openapi.yaml'
    path.write_text('''openapi: 3.1.0
info: {title: Example, version: 1.0.0}
paths:
  /users:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                required: [id]
                properties:
                  id: {type: integer}
''')
    spec = load_contract(path)
    response = httpx.Response(200, json={'id': 'wrong'})
    assert validate_response(spec, 'GET', 'https://api.example.com/users', response)
    assert validate_response(spec, 'GET', 'https://api.example.com/users', httpx.Response(200, json={'id': 3})) == []
    assert 'Undocumented' in validate_response(spec, 'GET', 'https://api.example.com/users', httpx.Response(404))[0]


@pytest.mark.asyncio
async def test_runner_with_contract():
    spec = {'paths': {'/ping': {'get': {'responses': {'200': {'content': {'application/json': {'schema': {'type': 'object', 'required': ['ok']}}}}}}}}}
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={'bad': True}))
    results = await run_suite([Case('ping', 'GET', 'https://example.com/ping')], transport=transport, contract=spec)
    assert not results[0].passed
    assert 'OpenAPI' in results[0].error
