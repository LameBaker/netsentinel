import socket

from app.main import create_app
from app.domain.models import RegisteredNode
from app.services.prober import tcp_probe


def test_tcp_probe_classifies_timeout_error(monkeypatch) -> None:
    node = RegisteredNode(
        node_id='node-timeout',
        name='timeout-node',
        host='203.0.113.10',
        port=443,
        region='us',
        enabled=True,
    )

    def raise_timeout(*args, **kwargs):
        raise socket.timeout('timed out')

    monkeypatch.setattr(socket, 'create_connection', raise_timeout)

    result = tcp_probe(node, timeout_s=0.01)

    assert result.status == 'down'
    assert result.error == 'timeout'


def test_non_positive_probe_timeout_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv('NETSENTINEL_PROBE_TIMEOUT_S', '0')
    app = create_app()
    assert app.state.probe_timeout_s == 1.5
