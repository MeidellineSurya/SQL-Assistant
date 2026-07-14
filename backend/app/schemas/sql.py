import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    connection_id: uuid.UUID
    question: str = Field(min_length=1)


class ValidateRequest(BaseModel):
    sql: str = Field(min_length=1)


class ValidateResponse(BaseModel):
    is_valid: bool
    error: str | None


class ExecuteRequest(BaseModel):
    history_id: uuid.UUID
    sql: str = Field(min_length=1)


class ExecutionResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool


class QueryHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    connection_id: uuid.UUID
    natural_language: str
    generated_sql: str
    is_valid: bool | None
    was_executed: bool
    row_count: int | None
    execution_ms: int | None
    error_message: str | None
    created_at: datetime


class QueryHistoryPage(BaseModel):
    items: list[QueryHistoryResponse]
    next_cursor: str | None


class ExecuteResponse(BaseModel):
    history: QueryHistoryResponse
    result: ExecutionResultResponse | None


class ExplainRequest(BaseModel):
    history_id: uuid.UUID
