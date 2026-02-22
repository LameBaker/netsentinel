from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_contract() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert payload['service'] == 'netsentinel'
    assert isinstance(payload['version'], str)
    assert isinstance(payload['timestamp'], str)
    assert isinstance(payload['uptime_s'], float)
