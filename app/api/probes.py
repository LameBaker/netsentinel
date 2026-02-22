from fastapi import APIRouter, HTTPException, Query, Request

from app.domain.models import ProbeResult, ProbeRunRequest, ProbeRunResponse, RegisteredNode

router = APIRouter(tags=['probes'])


def _resolve_targets(request: Request, node_id: str | None) -> list[RegisteredNode]:
    repository = request.app.state.repository
    if node_id is None:
        return repository.list_enabled_nodes()

    node = repository.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail='Node not found')
    return [node]


@router.post('/probes/run', response_model=ProbeRunResponse)
def run_probe(request: Request, payload: ProbeRunRequest | None = None) -> ProbeRunResponse:
    repository = request.app.state.repository
    probe_node = request.app.state.probe_node
    node_id = None if payload is None else payload.node_id
    targets = _resolve_targets(request, node_id)

    results: list[ProbeResult] = []
    for node in targets:
        result = probe_node(node)
        repository.add_probe_result(result)
        results.append(result)

    return ProbeRunResponse(results=results)


@router.get('/results', response_model=list[ProbeResult])
def list_results(
    request: Request,
    node_id: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=1000),
) -> list[ProbeResult]:
    repository = request.app.state.repository
    return repository.list_probe_results(node_id=node_id, limit=limit)
