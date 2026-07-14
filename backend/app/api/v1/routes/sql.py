import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.rate_limit import check_ai_rate_limit
from app.models.query import QueryHistory
from app.models.user import User
from app.schemas.sql import (
    ExecuteRequest,
    ExecuteResponse,
    ExplainRequest,
    GenerateRequest,
    QueryHistoryResponse,
    ValidateRequest,
    ValidateResponse,
)
from app.services import groq_service, history_service, sql_service
from app.services.connection_service import ConnectionNotFoundError
from app.services.groq_service import GroqServiceError
from app.services.history_service import HistoryItemNotFoundError
from app.services.sql_service import SqlServiceError

router = APIRouter(prefix="/sql", tags=["sql"])


@router.post(
    "/generate",
    response_model=QueryHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_ai_rate_limit)],
)
def generate(
    payload: GenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> QueryHistory:
    try:
        return sql_service.generate_sql(db, current_user.id, payload.connection_id, payload.question)
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found") from exc
    except SqlServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except GroqServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/validate", response_model=ValidateResponse)
def validate(payload: ValidateRequest) -> ValidateResponse:
    is_valid, error = sql_service.validate_sql(payload.sql)
    return ValidateResponse(is_valid=is_valid, error=error)


@router.post("/execute", response_model=ExecuteResponse)
def execute(
    payload: ExecuteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ExecuteResponse:
    try:
        history, result = sql_service.execute_sql(db, current_user.id, payload.history_id, payload.sql)
    except HistoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="history item not found") from exc
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found") from exc

    return ExecuteResponse(history=history, result=result)


@router.post("/explain", dependencies=[Depends(check_ai_rate_limit)])
def explain(
    payload: ExplainRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    try:
        history = history_service.get_history_item(db, current_user.id, payload.history_id)
    except HistoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="history item not found") from exc

    def event_stream():
        # Streaming has already started (200 sent) by the time any Groq
        # error can happen, so failures are reported as an SSE event rather
        # than an HTTP error status — there's no clean way to change the
        # status code mid-stream.
        try:
            for delta in groq_service.stream_explanation(history.natural_language, history.generated_sql):
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except GroqServiceError as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
