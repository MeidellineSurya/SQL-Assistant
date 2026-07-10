import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.sql import QueryHistoryPage, QueryHistoryResponse
from app.services import history_service
from app.services.history_service import HistoryItemNotFoundError, InvalidCursorError

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=QueryHistoryPage)
def list_history(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryHistoryPage:
    try:
        items, next_cursor = history_service.list_history(db, current_user.id, limit, cursor)
    except InvalidCursorError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return QueryHistoryPage(items=items, next_cursor=next_cursor)


@router.get("/{history_id}", response_model=QueryHistoryResponse)
def get_history_item(
    history_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> QueryHistoryResponse:
    try:
        return history_service.get_history_item(db, current_user.id, history_id)
    except HistoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(
    history_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> None:
    try:
        history_service.delete_history_item(db, current_user.id, history_id)
    except HistoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
