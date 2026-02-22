from fastapi import APIRouter, Request, status

from app.domain.models import Node, RegisteredNode

router = APIRouter(tags=['nodes'])


@router.post('/nodes', response_model=RegisteredNode, status_code=status.HTTP_201_CREATED)
def register_node(payload: Node, request: Request) -> RegisteredNode:
    repository = request.app.state.repository
    return repository.add_node(payload)


@router.get('/nodes', response_model=list[RegisteredNode])
def list_nodes(request: Request) -> list[RegisteredNode]:
    repository = request.app.state.repository
    return repository.list_nodes()
