from typing import Protocol

from app.domain.models import Node, ProbeResult


class Repository(Protocol):
    def add_node(self, node: Node) -> None:
        ...

    def list_nodes(self) -> list[Node]:
        ...

    def add_probe_result(self, result: ProbeResult) -> None:
        ...

    def list_probe_results(self, node_id: str | None = None) -> list[ProbeResult]:
        ...


class InMemoryRepository:
    def __init__(self) -> None:
        self._nodes: list[Node] = []
        self._results: list[ProbeResult] = []

    def add_node(self, node: Node) -> None:
        self._nodes.append(node)

    def list_nodes(self) -> list[Node]:
        return list(self._nodes)

    def add_probe_result(self, result: ProbeResult) -> None:
        self._results.append(result)

    def list_probe_results(self, node_id: str | None = None) -> list[ProbeResult]:
        if node_id is None:
            return list(self._results)
        return [result for result in self._results if result.node_id == node_id]
