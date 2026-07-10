from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.query import QueryHistory
from app.models.user import User
from app.schemas.sql import GenerateRequest, QueryHistoryResponse
from app.services import sql_service
from app.services.connection_service import ConnectionNotFoundError
from app.services.groq_service import GroqServiceError
from app.services.sql_service import SqlServiceError

router = APIRouter(prefix="/sql", tags=["sql"])


@router.post("/generate", response_model=QueryHistoryResponse, status_code=status.HTTP_201_CREATED)
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
