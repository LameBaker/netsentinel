import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.nodes import router as nodes_router
from app.api.probes import router as probes_router
from app.api.scheduler import router as scheduler_router
from app.core.logging import configure_logging
from app.services.prober import tcp_probe
from app.services.scheduler import MonitoringScheduler
from app.storage.repository import InMemoryRepository, RepositoryUnavailableError
from app.storage.sqlite_repository import SQLiteRepository

SERVICE_NAME = 'netsentinel'
SERVICE_VERSION = '0.1.0'


class RequestContextAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        defaults = {
            'request_id': '-',
            'method': '-',
            'path': '-',
            'status_code': '-',
            'duration_ms': '-',
        }
        extra = kwargs.get('extra', {})
        defaults.update(extra)
        kwargs['extra'] = defaults
        return msg, kwargs


def create_app(
    scheduler_interval_s: float | None = None,
    probe_timeout_s: float | None = None,
    probe_retry_count: int | None = None,
    storage_backend: str | None = None,
    sqlite_path: str | None = None,
    result_retention_per_node: int | None = None,
) -> FastAPI:
    configure_logging()
    interval = scheduler_interval_s
    if interval is None:
        raw_interval = os.getenv('NETSENTINEL_SCHEDULER_INTERVAL_S', '60')
        try:
            interval = float(raw_interval)
        except ValueError:
            interval = 60.0
    if interval <= 0:
        interval = 60.0
    elif interval < 1.0:
        interval = 1.0
    timeout_s = probe_timeout_s
    if timeout_s is None:
        raw_timeout = os.getenv('NETSENTINEL_PROBE_TIMEOUT_S', '1.5')
        try:
            timeout_s = float(raw_timeout)
        except ValueError:
            timeout_s = 1.5
    if timeout_s <= 0:
        timeout_s = 1.5
    elif timeout_s < 0.1:
        timeout_s = 0.1
    retry_count = probe_retry_count
    if retry_count is None:
        raw_retry = os.getenv('NETSENTINEL_PROBE_RETRY_COUNT', '0')
        try:
            retry_count = int(raw_retry)
        except ValueError:
            retry_count = 0
    retry_count = max(0, min(2, retry_count))
    backend = storage_backend or os.getenv('NETSENTINEL_STORAGE_BACKEND', 'memory')
    db_path = sqlite_path or os.getenv('NETSENTINEL_SQLITE_PATH', './netsentinel.sqlite3')
    retention = result_retention_per_node
    if retention is None:
        raw_retention = os.getenv('NETSENTINEL_RESULT_RETENTION_PER_NODE', '0')
        try:
            retention = int(raw_retention)
        except ValueError:
            retention = 0
    retention = max(0, retention)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app.state.scheduler.start()
        try:
            yield
        finally:
            await app.state.scheduler.stop()

    app = FastAPI(title='NetSentinel API', version=SERVICE_VERSION, lifespan=lifespan)
    app.state.service_name = SERVICE_NAME
    app.state.version = SERVICE_VERSION
    app.state.started_at = datetime.now(UTC)
    app.state.storage_backend = backend if backend == 'sqlite' else 'memory'
    app.state.storage_path_display = (
        Path(db_path).name if app.state.storage_backend == 'sqlite' else 'memory'
    )
    if backend == 'sqlite':
        app.state.repository = SQLiteRepository(db_path, retention_per_node=retention)
        try:
            app.state.repository.initialize()
        except RepositoryUnavailableError as exc:
            raise RuntimeError(
                f'Failed to initialize SQLite repository at {db_path}'
            ) from exc
    else:
        app.state.repository = InMemoryRepository()
    app.state.probe_timeout_s = timeout_s
    app.state.probe_retry_count = retry_count
    app.state.probe_node = lambda node: tcp_probe(node, timeout_s=app.state.probe_timeout_s)
    app.state.scheduler = MonitoringScheduler(app, interval)

    logger = RequestContextAdapter(logging.getLogger('netsentinel.http'), {})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', str(uuid4()))
        logger.exception(
            'unhandled_exception',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': 500,
                'duration_ms': '-',
            },
        )
        return JSONResponse(
            status_code=500,
            content={'detail': 'Internal Server Error'},
            headers={'X-Request-ID': request_id},
        )

    @app.middleware('http')
    async def request_logging(request: Request, call_next):
        request_id = request.headers.get('X-Request-ID', str(uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        response.headers['X-Request-ID'] = request_id
        logger.info(
            'request_complete',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
            },
        )
        return response

    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(nodes_router)
    app.include_router(probes_router)
    app.include_router(scheduler_router)
    return app


app = create_app()
