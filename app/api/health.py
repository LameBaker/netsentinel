from datetime import UTC, datetime

from fastapi import APIRouter, Request

router = APIRouter(tags=['system'])


@router.get('/health')
def health(request: Request) -> dict[str, object]:
    app_state = request.app.state
    uptime_seconds = (datetime.now(UTC) - app_state.started_at).total_seconds()

    return {
        'status': 'ok',
        'service': app_state.service_name,
        'version': app_state.version,
        'timestamp': datetime.now(UTC).isoformat(),
        'uptime_s': round(uptime_seconds, 3),
        'storage': app_state.storage_backend,
        'storage_path': app_state.storage_path_display,
        'last_repository_error': app_state.repository.get_last_error(),
    }
