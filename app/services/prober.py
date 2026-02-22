import socket
import time
from datetime import UTC, datetime

from app.domain.models import ProbeResult, RegisteredNode


def tcp_probe(node: RegisteredNode, timeout_s: float = 1.5) -> ProbeResult:
    started = time.perf_counter()
    try:
        with socket.create_connection((node.host, node.port), timeout=timeout_s):
            latency_ms = round((time.perf_counter() - started) * 1000, 3)
            return ProbeResult(
                node_id=node.node_id,
                status='up',
                latency_ms=latency_ms,
                checked_at=datetime.now(UTC),
            )
    except socket.timeout:
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        return ProbeResult(
            node_id=node.node_id,
            status='down',
            latency_ms=latency_ms,
            checked_at=datetime.now(UTC),
            error='timeout',
        )
    except OSError as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 3)
        return ProbeResult(
            node_id=node.node_id,
            status='down',
            latency_ms=latency_ms,
            checked_at=datetime.now(UTC),
            error=str(exc),
        )
