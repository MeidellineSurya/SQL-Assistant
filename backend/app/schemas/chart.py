import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SuggestChartRequest(BaseModel):
    query_id: uuid.UUID
    columns: list[str] = Field(min_length=1)
    sample_rows: list[list[Any]] = Field(default_factory=list, max_length=5)


class SuggestChartResponse(BaseModel):
    chart_type: str
    reasoning: str


class GenerateChartRequest(BaseModel):
    query_id: uuid.UUID
    chart_type: str
    columns: list[str] = Field(min_length=1)


class ChartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    query_id: uuid.UUID
    chart_type: str
    config_json: dict[str, Any]
    created_at: datetime
