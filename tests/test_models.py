import pytest
from pydantic import ValidationError

from app.domain.models import Node, ProbeResult


def test_node_requires_valid_port_range() -> None:
    with pytest.raises(ValidationError):
        Node(
            name='edge-eu-1',
            host='198.51.100.10',
            port=70000,
            region='eu',
        )


def test_probe_result_rejects_negative_latency() -> None:
    with pytest.raises(ValidationError):
        ProbeResult(
            node_id='node-1',
            status='up',
            latency_ms=-1.0,
        )
