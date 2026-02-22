from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.models import ProbeResult
from app.main import create_app


def test_register_and_list_nodes() -> None:
    app = create_app()
    client = TestClient(app)

    create_response = client.post(
        '/nodes',
        json={
            'name': 'edge-eu-1',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'eu',
            'enabled': True,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created['node_id']

    list_response = client.get('/nodes')
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload) == 1
    assert payload[0]['node_id'] == created['node_id']


def test_run_probe_by_node_id_stores_result() -> None:
    app = create_app()

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=12.5,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe
    client = TestClient(app)

    node = client.post(
        '/nodes',
        json={
            'name': 'edge-us-1',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    run_response = client.post('/probes/run', json={'node_id': node['node_id']})

    assert run_response.status_code == 200
    run_payload = run_response.json()
    assert len(run_payload['results']) == 1
    assert run_payload['results'][0]['node_id'] == node['node_id']

    results_response = client.get('/results', params={'node_id': node['node_id']})
    assert results_response.status_code == 200
    results_payload = results_response.json()
    assert len(results_payload) == 1
    assert results_payload[0]['latency_ms'] == 12.5


def test_run_probe_for_all_enabled_nodes_only() -> None:
    app = create_app()

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=5.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe
    client = TestClient(app)

    enabled = client.post(
        '/nodes',
        json={
            'name': 'enabled-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
            'enabled': True,
        },
    ).json()
    client.post(
        '/nodes',
        json={
            'name': 'disabled-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
            'enabled': False,
        },
    )

    run_response = client.post('/probes/run', json={})
    assert run_response.status_code == 200
    payload = run_response.json()
    assert len(payload['results']) == 1
    assert payload['results'][0]['node_id'] == enabled['node_id']


def test_run_probe_for_all_enabled_nodes_without_body() -> None:
    app = create_app()

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=4.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe
    client = TestClient(app)

    client.post(
        '/nodes',
        json={
            'name': 'enabled-node-no-body',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
            'enabled': True,
        },
    )

    run_response = client.post('/probes/run')
    assert run_response.status_code == 200
    payload = run_response.json()
    assert len(payload['results']) == 1


def test_results_limit_returns_latest_entries() -> None:
    app = create_app()

    def fake_probe(node) -> ProbeResult:
        fake_probe.counter += 1
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=float(fake_probe.counter),
            checked_at=datetime.now(UTC),
        )

    fake_probe.counter = 0
    app.state.probe_node = fake_probe

    client = TestClient(app)
    node = client.post(
        '/nodes',
        json={
            'name': 'edge-limit',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    client.post('/probes/run', json={'node_id': node['node_id']})
    client.post('/probes/run', json={'node_id': node['node_id']})

    response = client.get('/results', params={'node_id': node['node_id'], 'limit': 1})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]['latency_ms'] == 2.0


def test_results_limit_uses_checked_at_not_insertion_order() -> None:
    app = create_app()
    now = datetime.now(UTC)

    def fake_probe(node) -> ProbeResult:
        fake_probe.counter += 1
        if fake_probe.counter == 1:
            checked_at = now
            latency_ms = 10.0
        else:
            checked_at = now.replace(microsecond=max(now.microsecond - 1, 0))
            latency_ms = 20.0
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=latency_ms,
            checked_at=checked_at,
        )

    fake_probe.counter = 0
    app.state.probe_node = fake_probe
    client = TestClient(app)

    node = client.post(
        '/nodes',
        json={
            'name': 'edge-order',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    client.post('/probes/run', json={'node_id': node['node_id']})
    client.post('/probes/run', json={'node_id': node['node_id']})

    response = client.get('/results', params={'node_id': node['node_id'], 'limit': 1})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]['latency_ms'] == 10.0


def test_probe_retry_succeeds_on_second_attempt_when_enabled() -> None:
    app = create_app(scheduler_interval_s=60.0, probe_retry_count=1)
    calls = {'count': 0}

    def flaky_probe(node) -> ProbeResult:
        calls['count'] += 1
        if calls['count'] == 1:
            return ProbeResult(
                node_id=node.node_id,
                status='down',
                latency_ms=1.0,
                checked_at=datetime.now(UTC),
                error='connection_refused',
            )
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=2.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = flaky_probe
    client = TestClient(app)

    node = client.post(
        '/nodes',
        json={
            'name': 'retry-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    response = client.post('/probes/run', json={'node_id': node['node_id']})
    assert response.status_code == 200
    payload = response.json()
    assert payload['results'][0]['status'] == 'up'
    assert calls['count'] == 2


def test_probe_retry_returns_down_after_retries_exhausted() -> None:
    app = create_app(scheduler_interval_s=60.0, probe_retry_count=1)
    calls = {'count': 0}

    def always_down_probe(node) -> ProbeResult:
        calls['count'] += 1
        return ProbeResult(
            node_id=node.node_id,
            status='down',
            latency_ms=1.0,
            checked_at=datetime.now(UTC),
            error='connection_refused',
        )

    app.state.probe_node = always_down_probe
    client = TestClient(app)

    node = client.post(
        '/nodes',
        json={
            'name': 'retry-down-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    response = client.post('/probes/run', json={'node_id': node['node_id']})
    assert response.status_code == 200
    payload = response.json()
    assert payload['results'][0]['status'] == 'down'
    assert calls['count'] == 2


def test_results_supports_inclusive_time_window_filters() -> None:
    app = create_app()
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    checks = [base, base.replace(minute=1), base.replace(minute=2)]

    def fake_probe(node) -> ProbeResult:
        checked_at = checks.pop(0)
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=5.0,
            checked_at=checked_at,
        )

    app.state.probe_node = fake_probe
    client = TestClient(app)

    node = client.post(
        '/nodes',
        json={
            'name': 'window-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    client.post('/probes/run', json={'node_id': node['node_id']})
    client.post('/probes/run', json={'node_id': node['node_id']})
    client.post('/probes/run', json={'node_id': node['node_id']})

    response = client.get(
        '/results',
        params={
            'node_id': node['node_id'],
            'from': base.replace(minute=1).isoformat(),
            'to': base.replace(minute=2).isoformat(),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert payload[0]['checked_at'] == base.replace(minute=2).isoformat().replace(
        '+00:00', 'Z'
    )
    assert payload[1]['checked_at'] == base.replace(minute=1).isoformat().replace(
        '+00:00', 'Z'
    )


def test_results_summary_returns_expected_aggregates() -> None:
    app = create_app()
    base = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    scripted = [
        ('up', 10.0, None, base),
        ('down', 0.0, 'timeout', base.replace(minute=1)),
        ('up', 30.0, None, base.replace(minute=2)),
    ]

    def fake_probe(node) -> ProbeResult:
        status, latency_ms, error, checked_at = scripted.pop(0)
        return ProbeResult(
            node_id=node.node_id,
            status=status,
            latency_ms=latency_ms,
            checked_at=checked_at,
            error=error,
        )

    app.state.probe_node = fake_probe
    client = TestClient(app)
    node = client.post(
        '/nodes',
        json={
            'name': 'summary-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    client.post('/probes/run', json={'node_id': node['node_id']})
    client.post('/probes/run', json={'node_id': node['node_id']})
    client.post('/probes/run', json={'node_id': node['node_id']})

    response = client.get('/results/summary', params={'node_id': node['node_id']})
    assert response.status_code == 200
    payload = response.json()
    assert payload['total_checks'] == 3
    assert payload['up_checks'] == 2
    assert payload['down_checks'] == 1
    assert payload['availability_pct'] == 66.667
    assert payload['avg_latency_ms'] == 20.0
    assert payload['last_checked_at'] == base.replace(minute=2).isoformat().replace(
        '+00:00', 'Z'
    )


def test_results_summary_returns_zero_state_for_empty_window() -> None:
    app = create_app()
    at = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=7.0,
            checked_at=at,
        )

    app.state.probe_node = fake_probe
    client = TestClient(app)
    node = client.post(
        '/nodes',
        json={
            'name': 'summary-empty-window-node',
            'host': '127.0.0.1',
            'port': 443,
            'region': 'us',
        },
    ).json()

    client.post('/probes/run', json={'node_id': node['node_id']})

    response = client.get(
        '/results/summary',
        params={
            'node_id': node['node_id'],
            'from': at.replace(hour=11).isoformat(),
            'to': at.replace(hour=12).isoformat(),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['total_checks'] == 0
    assert payload['up_checks'] == 0
    assert payload['down_checks'] == 0
    assert payload['availability_pct'] == 0.0
    assert payload['avg_latency_ms'] is None
    assert payload['last_checked_at'] is None
