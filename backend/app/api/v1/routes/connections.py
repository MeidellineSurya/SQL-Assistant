import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.connection import DBConnection
from app.models.user import User
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestResult,
    ConnectionUpdate,
    SchemaCacheResponse,
)
from app.services import connection_service, schema_service
from app.services.connection_service import ConnectionNotFoundError

router = APIRouter(prefix="/connections", tags=["connections"])


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")


@router.get("", response_model=list[ConnectionResponse])
def list_connections(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[DBConnection]:
    return connection_service.list_connections(db, current_user.id)


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: ConnectionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DBConnection:
    return connection_service.create_connection(db, current_user.id, payload)


@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(
    connection_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> DBConnection:
    try:
        return connection_service.get_connection(db, current_user.id, connection_id)
    except ConnectionNotFoundError as exc:
        raise _not_found() from exc


@router.put("/{connection_id}", response_model=ConnectionResponse)
def update_connection(
    connection_id: uuid.UUID,
    payload: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DBConnection:
    try:
        return connection_service.update_connection(db, current_user.id, connection_id, payload)
    except ConnectionNotFoundError as exc:
        raise _not_found() from exc


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    try:
        connection_service.delete_connection(db, current_user.id, connection_id)
    except ConnectionNotFoundError as exc:
        raise _not_found() from exc


@router.post("/{connection_id}/test", response_model=ConnectionTestResult)
def test_connection(
    connection_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ConnectionTestResult:
    try:
        return connection_service.test_connection(db, current_user.id, connection_id)
    except ConnectionNotFoundError as exc:
        raise _not_found() from exc


@router.post("/{connection_id}/schema", response_model=SchemaCacheResponse)
def refresh_schema(
    connection_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> SchemaCacheResponse:
    try:
        conn = schema_service.refresh_schema(db, current_user.id, connection_id)
    except ConnectionNotFoundError as exc:
        raise _not_found() from exc

    return SchemaCacheResponse(schema_cache=conn.schema_cache, schema_cached_at=conn.schema_cached_at)
