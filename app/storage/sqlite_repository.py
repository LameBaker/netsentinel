import sqlite3
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.domain.models import Node, ProbeResult, RegisteredNode
from app.storage.repository import (
    RepositoryDuplicateError,
    RepositoryUnavailableError,
)


class SQLiteRepository:
    def __init__(self, db_path: str, retention_per_node: int = 0) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._retention_per_node = max(0, retention_per_node)
        self._last_error: str | None = None

    def initialize(self) -> None:
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        def init(conn: sqlite3.Connection) -> None:
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
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_nodes_host_port_region
                ON nodes(host, port, region)
                """
            )

        self._run_write(init)

    def add_node(self, node: Node) -> RegisteredNode:
        stored = RegisteredNode(node_id=str(uuid4()), **node.model_dump())
        def write(conn: sqlite3.Connection) -> None:
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
        self._run_write(write)
        return stored

    def list_nodes(self) -> list[RegisteredNode]:
        def read(conn: sqlite3.Connection) -> list[sqlite3.Row]:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                """
                SELECT node_id, name, host, port, region, enabled
                FROM nodes
                ORDER BY rowid ASC
                """
            ).fetchall()
        rows = self._run_read(read)
        return [self._row_to_node(row) for row in rows]

    def get_node(self, node_id: str) -> RegisteredNode | None:
        def read(conn: sqlite3.Connection) -> sqlite3.Row | None:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                """
                SELECT node_id, name, host, port, region, enabled
                FROM nodes
                WHERE node_id = ?
                """,
                (node_id,),
            ).fetchone()
        row = self._run_read(read)
        if row is None:
            return None
        return self._row_to_node(row)

    def list_enabled_nodes(self) -> list[RegisteredNode]:
        def read(conn: sqlite3.Connection) -> list[sqlite3.Row]:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                """
                SELECT node_id, name, host, port, region, enabled
                FROM nodes
                WHERE enabled = 1
                ORDER BY rowid ASC
                """
            ).fetchall()
        rows = self._run_read(read)
        return [self._row_to_node(row) for row in rows]

    def add_probe_result(self, result: ProbeResult) -> None:
        checked_at = result.checked_at.astimezone(UTC).isoformat()
        def write(conn: sqlite3.Connection) -> None:
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
            if self._retention_per_node > 0:
                conn.execute(
                    """
                    DELETE FROM probe_results
                    WHERE id IN (
                        SELECT id FROM probe_results
                        WHERE node_id = ?
                        ORDER BY checked_at DESC, id DESC
                        LIMIT -1 OFFSET ?
                    )
                    """,
                    (result.node_id, self._retention_per_node),
                )
        self._run_write(write)

    def count_probe_results(self) -> int:
        def read(conn: sqlite3.Connection) -> int:
            row = conn.execute('SELECT COUNT(*) FROM probe_results').fetchone()
            return int(row[0])
        return self._run_read(read)

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

        def read(conn: sqlite3.Connection) -> list[sqlite3.Row]:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()
        rows = self._run_read(read)

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

    def get_last_error(self) -> str | None:
        return self._last_error

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=5.0)
        conn.execute('PRAGMA busy_timeout = 5000')
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _run_write(self, fn):
        for attempt in range(3):
            try:
                with self._lock, self._connect() as conn:
                    fn(conn)
                self._last_error = None
                return
            except sqlite3.IntegrityError as exc:
                self._last_error = str(exc)
                raise RepositoryDuplicateError('Duplicate node registration') from exc
            except sqlite3.OperationalError as exc:
                if self._is_locked(exc) and attempt < 2:
                    time.sleep(0.05)
                    continue
                self._last_error = str(exc)
                raise RepositoryUnavailableError('SQLite write operation failed') from exc
            except sqlite3.Error as exc:
                self._last_error = str(exc)
                raise RepositoryUnavailableError('SQLite write operation failed') from exc

    def _run_read(self, fn):
        for attempt in range(3):
            try:
                with self._lock, self._connect() as conn:
                    result = fn(conn)
                self._last_error = None
                return result
            except sqlite3.OperationalError as exc:
                if self._is_locked(exc) and attempt < 2:
                    time.sleep(0.05)
                    continue
                self._last_error = str(exc)
                raise RepositoryUnavailableError('SQLite read operation failed') from exc
            except sqlite3.Error as exc:
                self._last_error = str(exc)
                raise RepositoryUnavailableError('SQLite read operation failed') from exc

    @staticmethod
    def _is_locked(exc: sqlite3.OperationalError) -> bool:
        message = str(exc).lower()
        return 'database is locked' in message or 'database table is locked' in message

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
