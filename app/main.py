import logging
import time
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.core.logging import configure_logging
from app.storage.repository import InMemoryRepository

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


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title='NetSentinel API', version=SERVICE_VERSION)
    app.state.service_name = SERVICE_NAME
    app.state.version = SERVICE_VERSION
    app.state.started_at = datetime.now(UTC)
    app.state.repository = InMemoryRepository()

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
    return app


app = create_app()
