from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.models import ProbeResult
from app.main import create_app


def test_sqlite_storage_persists_data_across_app_restart(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / 'netsentinel.sqlite3'
    monkeypatch.setenv('NETSENTINEL_STORAGE_BACKEND', 'sqlite')
    monkeypatch.setenv('NETSENTINEL_SQLITE_PATH', str(db_path))

    app_one = create_app(scheduler_interval_s=60.0)

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=11.0,
            checked_at=datetime.now(UTC),
        )

    app_one.state.probe_node = fake_probe

    with TestClient(app_one) as client:
        created = client.post(
            '/nodes',
            json={
                'name': 'persistent-node',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
                'enabled': True,
            },
        ).json()
        run_response = client.post('/probes/run', json={'node_id': created['node_id']})
        assert run_response.status_code == 200

    app_two = create_app(scheduler_interval_s=60.0)
    app_two.state.probe_node = fake_probe

    with TestClient(app_two) as client:
        nodes_response = client.get('/nodes')
        assert nodes_response.status_code == 200
        nodes_payload = nodes_response.json()
        assert len(nodes_payload) == 1
        assert nodes_payload[0]['node_id'] == created['node_id']

        results_response = client.get('/results', params={'node_id': created['node_id']})
        assert results_response.status_code == 200
        results_payload = results_response.json()
        assert len(results_payload) == 1
        assert results_payload[0]['latency_ms'] == 11.0


def test_storage_backend_defaults_to_memory_for_unknown_value(monkeypatch) -> None:
    monkeypatch.setenv('NETSENTINEL_STORAGE_BACKEND', 'invalid-backend')
    app = create_app()

    response = TestClient(app).get('/health')
    assert response.status_code == 200


def test_sqlite_duplicate_node_registration_returns_409(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / 'netsentinel.sqlite3'
    monkeypatch.setenv('NETSENTINEL_STORAGE_BACKEND', 'sqlite')
    monkeypatch.setenv('NETSENTINEL_SQLITE_PATH', str(db_path))

    app = create_app(scheduler_interval_s=60.0)
    with TestClient(app) as client:
        first = client.post(
            '/nodes',
            json={
                'name': 'dup-node-1',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
            },
        )
        assert first.status_code == 201

        duplicate = client.post(
            '/nodes',
            json={
                'name': 'dup-node-2',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
            },
        )
        assert duplicate.status_code == 409
        assert duplicate.json()['detail'] == 'Node already exists'


def test_sqlite_retention_keeps_latest_results_per_node(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / 'netsentinel.sqlite3'
    monkeypatch.setenv('NETSENTINEL_STORAGE_BACKEND', 'sqlite')
    monkeypatch.setenv('NETSENTINEL_SQLITE_PATH', str(db_path))
    monkeypatch.setenv('NETSENTINEL_RESULT_RETENTION_PER_NODE', '1')

    app = create_app(scheduler_interval_s=60.0)
    call = {'n': 0}

    def fake_probe(node) -> ProbeResult:
        call['n'] += 1
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=float(call['n']),
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe

    with TestClient(app) as client:
        node = client.post(
            '/nodes',
            json={
                'name': 'ret-node',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
            },
        ).json()

        client.post('/probes/run', json={'node_id': node['node_id']})
        client.post('/probes/run', json={'node_id': node['node_id']})

        results_response = client.get('/results', params={'node_id': node['node_id']})
        assert results_response.status_code == 200
        results = results_response.json()
        assert len(results) == 1
        assert results[0]['latency_ms'] == 2.0


def test_sqlite_init_failure_fails_fast_with_clear_message(tmp_path) -> None:
    db_dir = tmp_path / 'dbdir'
    db_dir.mkdir()

    try:
        create_app(
            scheduler_interval_s=60.0,
            storage_backend='sqlite',
            sqlite_path=str(db_dir),
        )
        assert False, 'Expected RuntimeError for SQLite init failure'
    except RuntimeError as exc:
        assert 'Failed to initialize SQLite repository' in str(exc)
