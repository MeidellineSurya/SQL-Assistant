from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.chart import Chart
from app.models.user import User
from app.schemas.chart import (
    ChartResponse,
    GenerateChartRequest,
    SuggestChartRequest,
    SuggestChartResponse,
)
from app.services import chart_service
from app.services.chart_service import ChartServiceError
from app.services.groq_service import GroqServiceError
from app.services.history_service import HistoryItemNotFoundError

router = APIRouter(prefix="/charts", tags=["charts"])


@router.post("/suggest", response_model=SuggestChartResponse)
def suggest(
    payload: SuggestChartRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> SuggestChartResponse:
    try:
        chart_type, reasoning = chart_service.suggest_chart_type(
            db, current_user.id, payload.query_id, payload.columns, payload.sample_rows
        )
    except HistoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="query not found") from exc
    except GroqServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ChartServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SuggestChartResponse(chart_type=chart_type, reasoning=reasoning)


@router.post("/generate", response_model=ChartResponse, status_code=status.HTTP_201_CREATED)
def generate(
    payload: GenerateChartRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Chart:
    try:
        return chart_service.generate_chart(
            db, current_user.id, payload.query_id, payload.chart_type, payload.columns
        )
    except HistoryItemNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="query not found") from exc
    except GroqServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except ChartServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
