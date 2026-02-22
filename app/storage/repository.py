from datetime import UTC, datetime
from typing import Protocol

from uuid import uuid4

from app.domain.models import Node, ProbeResult, ProbeResultsSummary, RegisteredNode


class RepositoryError(Exception):
    """Base repository error."""


class RepositoryDuplicateError(RepositoryError):
    """Entity already exists."""


class RepositoryUnavailableError(RepositoryError):
    """Repository backend unavailable."""


class Repository(Protocol):
    def add_node(self, node: Node) -> RegisteredNode:
        ...

    def list_nodes(self) -> list[RegisteredNode]:
        ...

    def get_node(self, node_id: str) -> RegisteredNode | None:
        ...

    def list_enabled_nodes(self) -> list[RegisteredNode]:
        ...

    def add_probe_result(self, result: ProbeResult) -> None:
        ...

    def list_probe_results(
        self,
        node_id: str | None = None,
        limit: int | None = None,
        checked_from: datetime | None = None,
        checked_to: datetime | None = None,
    ) -> list[ProbeResult]:
        ...

    def summarize_probe_results(
        self,
        node_id: str | None = None,
        checked_from: datetime | None = None,
        checked_to: datetime | None = None,
    ) -> ProbeResultsSummary:
        ...

    def count_probe_results(self) -> int:
        ...

    def get_last_error(self) -> str | None:
        ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._nodes: list[RegisteredNode] = []
        self._results: list[ProbeResult] = []

    def add_node(self, node: Node) -> RegisteredNode:
        stored = RegisteredNode(node_id=str(uuid4()), **node.model_dump())
        self._nodes.append(stored)
        return stored

    def list_nodes(self) -> list[RegisteredNode]:
        return list(self._nodes)

    def get_node(self, node_id: str) -> RegisteredNode | None:
        for node in self._nodes:
            if node.node_id == node_id:
                return node
        return None

    def list_enabled_nodes(self) -> list[RegisteredNode]:
        return [node for node in self._nodes if node.enabled]

    def add_probe_result(self, result: ProbeResult) -> None:
        self._results.append(result)

    def list_probe_results(
        self,
        node_id: str | None = None,
        limit: int | None = None,
        checked_from: datetime | None = None,
        checked_to: datetime | None = None,
    ) -> list[ProbeResult]:
        results = self._filter_probe_results(
            node_id=node_id,
            checked_from=checked_from,
            checked_to=checked_to,
        )

        ordered = sorted(results, key=lambda item: item.checked_at, reverse=True)
        if limit is None:
            return ordered
        return ordered[:limit]

    def summarize_probe_results(
        self,
        node_id: str | None = None,
        checked_from: datetime | None = None,
        checked_to: datetime | None = None,
    ) -> ProbeResultsSummary:
        results = self._filter_probe_results(
            node_id=node_id,
            checked_from=checked_from,
            checked_to=checked_to,
        )
        total_checks = len(results)
        up_checks = sum(1 for result in results if result.status == 'up')
        down_checks = total_checks - up_checks
        availability_pct = 0.0
        if total_checks > 0:
            availability_pct = round((up_checks / total_checks) * 100, 3)
        up_latencies = [result.latency_ms for result in results if result.status == 'up']
        avg_latency_ms = None
        if up_latencies:
            avg_latency_ms = round(sum(up_latencies) / len(up_latencies), 3)
        last_checked_at = None
        if results:
            last_checked_at = max(
                self._normalize_datetime(result.checked_at) for result in results
            )
        return ProbeResultsSummary(
            total_checks=total_checks,
            up_checks=up_checks,
            down_checks=down_checks,
            availability_pct=availability_pct,
            avg_latency_ms=avg_latency_ms,
            last_checked_at=last_checked_at,
        )

    def count_probe_results(self) -> int:
        return len(self._results)

    def get_last_error(self) -> str | None:
        return None

    def _filter_probe_results(
        self,
        node_id: str | None,
        checked_from: datetime | None,
        checked_to: datetime | None,
    ) -> list[ProbeResult]:
        from_bound = self._normalize_datetime(checked_from)
        to_bound = self._normalize_datetime(checked_to)
        filtered = list(self._results)
        if node_id is not None:
            filtered = [result for result in filtered if result.node_id == node_id]
        if from_bound is not None:
            filtered = [
                result
                for result in filtered
                if self._normalize_datetime(result.checked_at) >= from_bound
            ]
        if to_bound is not None:
            filtered = [
                result
                for result in filtered
                if self._normalize_datetime(result.checked_at) <= to_bound
            ]
        return filtered

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
