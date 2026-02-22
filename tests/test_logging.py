import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.logging import ContextSafeFormatter, configure_logging
from app.main import create_app


def test_request_id_header_is_present() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.headers.get('X-Request-ID')


def test_incoming_request_id_is_preserved() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get('/health', headers={'X-Request-ID': 'client-id-123'})

    assert response.status_code == 200
    assert response.headers.get('X-Request-ID') == 'client-id-123'


def test_request_id_header_is_present_on_unhandled_exception() -> None:
    app = create_app()

    @app.get('/boom')
    def boom() -> dict[str, str]:
        raise RuntimeError('boom')

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get('/boom')

    assert response.status_code == 500
    assert response.headers.get('X-Request-ID')


def test_custom_exception_handler_is_respected_by_middleware() -> None:
    app = create_app()

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=418, content={'detail': str(exc)})

    @app.get('/value-error')
    def value_error() -> dict[str, str]:
        raise ValueError('custom-handler')

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get('/value-error')

    assert response.status_code == 418
    assert response.json()['detail'] == 'custom-handler'
    assert response.headers.get('X-Request-ID')


def test_context_safe_formatter_handles_records_without_request_context() -> None:
    formatter = ContextSafeFormatter(
        "%(request_id)s %(method)s %(path)s %(status_code)s %(duration_ms)s %(message)s"
    )
    record = logging.LogRecord(
        name='uvicorn.access',
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='external logger message',
        args=(),
        exc_info=None,
    )

    rendered = formatter.format(record)

    assert rendered.startswith('- - - - - external logger message')


def test_configure_logging_does_not_override_root_handlers() -> None:
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level

    class SentinelFormatter(logging.Formatter):
        pass

    sentinel_handler = logging.StreamHandler()
    sentinel_handler.setFormatter(SentinelFormatter('%(message)s'))

    try:
        root_logger.handlers = [sentinel_handler]
        configure_logging()
        assert isinstance(root_logger.handlers[0].formatter, SentinelFormatter)
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
