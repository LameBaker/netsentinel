from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.models import ProbeResult
from app.main import create_app


def test_metrics_endpoint_contract_and_values() -> None:
    app = create_app(scheduler_interval_s=60.0)

    def fake_probe(node) -> ProbeResult:
        return ProbeResult(
            node_id=node.node_id,
            status='up',
            latency_ms=9.0,
            checked_at=datetime.now(UTC),
        )

    app.state.probe_node = fake_probe

    with TestClient(app) as client:
        node = client.post(
            '/nodes',
            json={
                'name': 'metrics-node',
                'host': '127.0.0.1',
                'port': 443,
                'region': 'us',
                'enabled': True,
            },
        ).json()

        client.post('/scheduler/run-once')

        response = client.get('/metrics')
        assert response.status_code == 200
        payload = response.json()

        assert payload['uptime_s'] >= 0
        assert payload['nodes_total'] == 1
        assert payload['nodes_enabled'] == 1
        assert payload['probe_results_total'] == 1
        assert payload['scheduler']['successful_cycles'] >= 1
        assert payload['scheduler']['failed_cycles'] == 0
        assert payload['scheduler']['consecutive_failures'] == 0
        assert payload['scheduler']['last_cycle_duration_ms'] is not None
        assert payload['storage'] in ('memory', 'sqlite')
        assert isinstance(payload['storage_path'], str)
        assert payload['last_repository_error'] is None
        assert payload['service'] == 'netsentinel'
        assert payload['version']
        assert node['node_id']
