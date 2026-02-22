import logging


class ContextSafeFormatter(logging.Formatter):
    """Formatter that tolerates records without request context fields."""

    _defaults = {
        'request_id': '-',
        'method': '-',
        'path': '-',
        'status_code': '-',
        'duration_ms': '-',
    }

    def format(self, record: logging.LogRecord) -> str:
        for key, default in self._defaults.items():
            if not hasattr(record, key):
                setattr(record, key, default)
        return super().format(record)


def configure_logging() -> None:
    """Configure structured logging only for NetSentinel loggers."""
    fmt = (
        '%(asctime)s %(levelname)s %(name)s '
        'request_id=%(request_id)s method=%(method)s path=%(path)s '
        'status_code=%(status_code)s duration_ms=%(duration_ms)s message=%(message)s'
    )
    formatter = ContextSafeFormatter(fmt)
    logger = logging.getLogger('netsentinel')
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        for handler in logger.handlers:
            handler.setFormatter(formatter)
        return

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
