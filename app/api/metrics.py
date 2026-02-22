from datetime import UTC, datetime

from fastapi import APIRouter, Request

router = APIRouter(tags=['system'])


@router.get('/metrics')
def metrics(request: Request) -> dict[str, object]:
    app_state = request.app.state
    repository = app_state.repository
    scheduler = app_state.scheduler

    uptime_seconds = (datetime.now(UTC) - app_state.started_at).total_seconds()
    nodes_total = len(repository.list_nodes())
    nodes_enabled = len(repository.list_enabled_nodes())
    probe_results_total = repository.count_probe_results()

    return {
        'service': app_state.service_name,
        'version': app_state.version,
        'uptime_s': round(uptime_seconds, 3),
        'nodes_total': nodes_total,
        'nodes_enabled': nodes_enabled,
        'probe_results_total': probe_results_total,
        'scheduler': {
            'successful_cycles': scheduler.successful_cycles,
            'failed_cycles': scheduler.failed_cycles,
            'consecutive_failures': scheduler.consecutive_failures,
            'last_cycle_duration_ms': scheduler.last_cycle_duration_ms,
        },
    }
