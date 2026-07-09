import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConnectionCreate(BaseModel):
    name: str = Field(min_length=1)
    host: str
    port: int = 5432
    database_name: str
    username: str
    password: str
    ssl_mode: str = "require"


class ConnectionUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_mode: str | None = None


class ConnectionResponse(BaseModel):
    """Never includes the password, encrypted or otherwise."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    host: str
    port: int
    database_name: str
    username: str
    ssl_mode: str
    schema_cached_at: datetime | None
    created_at: datetime


class ConnectionTestResult(BaseModel):
    success: bool
    latency_ms: int | None = None
    error: str | None = None


class SchemaColumn(BaseModel):
    name: str
    data_type: str
    is_nullable: bool


class SchemaTable(BaseModel):
    name: str
    columns: list[SchemaColumn]


class SchemaSnapshot(BaseModel):
    tables: list[SchemaTable]
    cached_at: datetime


class SchemaCacheResponse(BaseModel):
    schema_cache: dict[str, Any] | None
    schema_cached_at: datetime | None
