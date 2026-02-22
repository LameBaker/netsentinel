from fastapi import APIRouter, Request

router = APIRouter(tags=['scheduler'])


@router.get('/scheduler/status')
def scheduler_status(request: Request) -> dict[str, object]:
    scheduler = request.app.state.scheduler
    return {
        'running': scheduler.running,
        'interval_s': scheduler.interval_s,
        'last_run': None if scheduler.last_run is None else scheduler.last_run.isoformat(),
        'last_error': scheduler.last_error,
        'last_cycle_duration_ms': scheduler.last_cycle_duration_ms,
        'successful_cycles': scheduler.successful_cycles,
        'failed_cycles': scheduler.failed_cycles,
        'consecutive_failures': scheduler.consecutive_failures,
    }


@router.post('/scheduler/run-once')
async def scheduler_run_once(request: Request) -> dict[str, object]:
    scheduler = request.app.state.scheduler
    count = await scheduler.run_once()
    return {'results_count': count}
