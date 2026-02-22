from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Request

from app.domain.models import (
    ProbeResult,
    ProbeResultsSummary,
    ProbeRunRequest,
    ProbeRunResponse,
    RegisteredNode,
)

router = APIRouter(tags=['probes'])


def _resolve_targets(repository, node_id: str | None) -> list[RegisteredNode]:
    if node_id is None:
        return repository.list_enabled_nodes()

    node = repository.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail='Node not found')
    return [node]


def run_probe_cycle(app, node_id: str | None) -> list[ProbeResult]:
    repository = app.state.repository
    probe_node = app.state.probe_node
    retry_count = getattr(app.state, 'probe_retry_count', 0)
    targets = _resolve_targets(repository, node_id)

    results: list[ProbeResult] = []
    for node in targets:
        attempt = 0
        while True:
            result = probe_node(node)
            if result.status == 'up' or attempt >= retry_count:
                break
            attempt += 1
        repository.add_probe_result(result)
        results.append(result)
    return results


@router.post('/probes/run', response_model=ProbeRunResponse)
def run_probe(request: Request, payload: ProbeRunRequest | None = None) -> ProbeRunResponse:
    node_id = None if payload is None else payload.node_id
    results = run_probe_cycle(request.app, node_id)
    return ProbeRunResponse(results=results)


@router.get('/results', response_model=list[ProbeResult])
def list_results(
    request: Request,
    node_id: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=1000),
    from_: datetime | None = Query(default=None, alias='from'),
    to: datetime | None = Query(default=None),
) -> list[ProbeResult]:
    repository = request.app.state.repository
    return repository.list_probe_results(
        node_id=node_id,
        limit=limit,
        checked_from=from_,
        checked_to=to,
    )


@router.get('/results/summary', response_model=ProbeResultsSummary)
def summarize_results(
    request: Request,
    node_id: str | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias='from'),
    to: datetime | None = Query(default=None),
) -> ProbeResultsSummary:
    repository = request.app.state.repository
    return repository.summarize_probe_results(
        node_id=node_id,
        checked_from=from_,
        checked_to=to,
    )
