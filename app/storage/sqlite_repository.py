import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.domain.models import Node, ProbeResult, RegisteredNode


class SQLiteRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()

    def initialize(self) -> None:
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    node_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    region TEXT NOT NULL,
                    enabled INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS probe_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    checked_at TEXT NOT NULL,
                    error TEXT,
                    FOREIGN KEY(node_id) REFERENCES nodes(node_id)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_probe_results_node_checked_at
                ON probe_results(node_id, checked_at DESC)
                """
            )

    def add_node(self, node: Node) -> RegisteredNode:
        stored = RegisteredNode(node_id=str(uuid4()), **node.model_dump())
        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.execute(
                """
                INSERT INTO nodes(node_id, name, host, port, region, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    stored.node_id,
                    stored.name,
                    stored.host,
                    stored.port,
                    stored.region,
                    1 if stored.enabled else 0,
                ),
            )
        return stored

    def list_nodes(self) -> list[RegisteredNode]:
        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT node_id, name, host, port, region, enabled
                FROM nodes
                ORDER BY rowid ASC
                """
            ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def get_node(self, node_id: str) -> RegisteredNode | None:
        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT node_id, name, host, port, region, enabled
                FROM nodes
                WHERE node_id = ?
                """,
                (node_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_node(row)

    def list_enabled_nodes(self) -> list[RegisteredNode]:
        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT node_id, name, host, port, region, enabled
                FROM nodes
                WHERE enabled = 1
                ORDER BY rowid ASC
                """
            ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def add_probe_result(self, result: ProbeResult) -> None:
        checked_at = result.checked_at.astimezone(UTC).isoformat()
        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.execute(
                """
                INSERT INTO probe_results(node_id, status, latency_ms, checked_at, error)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    result.node_id,
                    result.status,
                    result.latency_ms,
                    checked_at,
                    result.error,
                ),
            )

    def count_probe_results(self) -> int:
        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            row = conn.execute('SELECT COUNT(*) FROM probe_results').fetchone()
        return int(row[0])

    def list_probe_results(
        self, node_id: str | None = None, limit: int | None = None
    ) -> list[ProbeResult]:
        query = (
            "SELECT node_id, status, latency_ms, checked_at, error "
            "FROM probe_results"
        )
        params: list[object] = []

        if node_id is not None:
            query += ' WHERE node_id = ?'
            params.append(node_id)

        query += ' ORDER BY checked_at DESC'

        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)

        with self._lock, sqlite3.connect(self._db_path, timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [
            ProbeResult(
                node_id=row['node_id'],
                status=row['status'],
                latency_ms=row['latency_ms'],
                checked_at=datetime.fromisoformat(row['checked_at']),
                error=row['error'],
            )
            for row in rows
        ]

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> RegisteredNode:
        return RegisteredNode(
            node_id=row['node_id'],
            name=row['name'],
            host=row['host'],
            port=row['port'],
            region=row['region'],
            enabled=bool(row['enabled']),
        )
