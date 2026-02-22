import asyncio
import time
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.models import Node, ProbeResult
from app.main import create_app


def test_scheduler_status_endpoint_reports_running() -> None:
    app = create_app(scheduler_interval_s=0.2)

    with TestClient(app) as client:
        response = client.get('/scheduler/status')

    assert response.status_code == 200
    payload = response.json()
    assert payload['running'] is True
    assert payload['interval_s'] == 0.2
    assert payload['last_run'] is None


def test_scheduler_run_once_triggers_probe_cycle() -> None:
    app = create_app(scheduler_interval_s=60.0)

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=7.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe

    with TestClient(app) as client:
        node = client.post(
            '/nodes',
            json={
                'name': 'scheduler-node',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
            },
        ).json()

        run_response = client.post('/scheduler/run-once')
        assert run_response.status_code == 200
        run_payload = run_response.json()
        assert run_payload['results_count'] == 1

        results_response = client.get('/results', params={'node_id': node['node_id']})
        assert results_response.status_code == 200
        assert len(results_response.json()) == 1


def test_scheduler_loop_runs_automatically_on_interval() -> None:
    app = create_app(scheduler_interval_s=0.05)

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=3.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe

    with TestClient(app) as client:
        node = client.post(
            '/nodes',
            json={
                'name': 'auto-node',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
            },
        ).json()

        deadline = time.time() + 1.5
        while time.time() < deadline:
            results_response = client.get('/results', params={'node_id': node['node_id']})
            if len(results_response.json()) >= 2:
                break
            time.sleep(0.05)

        assert len(results_response.json()) >= 2


def test_scheduler_stop_is_fast_even_with_large_interval() -> None:
    app = create_app(scheduler_interval_s=30.0)

    started = time.perf_counter()
    with TestClient(app):
        pass
    elapsed = time.perf_counter() - started

    assert elapsed < 1.0


def test_scheduler_run_once_is_serialized() -> None:
    app = create_app(scheduler_interval_s=60.0)
    active = 0
    max_active = 0

    def fake_probe(node) -> ProbeResult:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        time.sleep(0.05)
        active -= 1
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=1.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe
    repository = app.state.repository
    node = repository.add_node(
        Node(name='n', host='127.0.0.1', port=443, region='us', enabled=True)
    )
    assert node.node_id

    async def run_two() -> None:
        await asyncio.gather(app.state.scheduler.run_once(), app.state.scheduler.run_once())

    asyncio.run(run_two())
    assert max_active == 1


def test_invalid_scheduler_interval_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv('NETSENTINEL_SCHEDULER_INTERVAL_S', 'not-a-number')
    app = create_app()
    assert app.state.scheduler.interval_s == 60.0


def test_non_positive_scheduler_interval_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv('NETSENTINEL_SCHEDULER_INTERVAL_S', '0')
    app = create_app()
    assert app.state.scheduler.interval_s == 60.0


def test_scheduler_status_includes_reliability_counters() -> None:
    app = create_app(scheduler_interval_s=60.0)

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=5.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe

    with TestClient(app) as client:
        client.post(
            '/nodes',
            json={
                'name': 'counter-node',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
            },
        )
        run_response = client.post('/scheduler/run-once')
        assert run_response.status_code == 200

        status_response = client.get('/scheduler/status')
        assert status_response.status_code == 200
        payload = status_response.json()
        assert payload['successful_cycles'] >= 1
        assert payload['failed_cycles'] == 0
        assert payload['consecutive_failures'] == 0
        assert payload['last_cycle_duration_ms'] is not None


def test_scheduler_failure_counters_increment_on_cycle_error() -> None:
    app = create_app(scheduler_interval_s=60.0)

    class FailingRepository:
        def list_enabled_nodes(self):
            raise RuntimeError('repository unavailable')

    app.state.repository = FailingRepository()

    with TestClient(app, raise_server_exceptions=False) as client:
        run_response = client.post('/scheduler/run-once')
        assert run_response.status_code == 500

        status_response = client.get('/scheduler/status')
        assert status_response.status_code == 200
        payload = status_response.json()
        assert payload['failed_cycles'] >= 1
        assert payload['consecutive_failures'] >= 1
        assert payload['last_error'] is not None
