from typing import Protocol

from uuid import uuid4

from app.domain.models import Node, ProbeResult, RegisteredNode


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
        self, node_id: str | None = None, limit: int | None = None
    ) -> list[ProbeResult]:
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
        self, node_id: str | None = None, limit: int | None = None
    ) -> list[ProbeResult]:
        if node_id is None:
            results = list(self._results)
        else:
            results = [result for result in self._results if result.node_id == node_id]

        ordered = sorted(results, key=lambda item: item.checked_at, reverse=True)
        if limit is None:
            return ordered
        return ordered[:limit]
