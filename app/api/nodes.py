from fastapi import APIRouter, HTTPException, Request, status

from app.domain.models import Node, RegisteredNode
from app.storage.repository import RepositoryDuplicateError

router = APIRouter(tags=['nodes'])


@router.post('/nodes', response_model=RegisteredNode, status_code=status.HTTP_201_CREATED)
def register_node(payload: Node, request: Request) -> RegisteredNode:
    repository = request.app.state.repository
    try:
        return repository.add_node(payload)
    except RepositoryDuplicateError as exc:
        raise HTTPException(status_code=409, detail='Node already exists') from exc


@router.get('/nodes', response_model=list[RegisteredNode])
def list_nodes(request: Request) -> list[RegisteredNode]:
    repository = request.app.state.repository
    return repository.list_nodes()
