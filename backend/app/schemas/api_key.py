import uuid
from datetime import datetime

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str
    rate_limit: int = 1000


class ApiKeyResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    key_prefix: str
    rate_limit: int
    is_active: bool
    created_at: datetime


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Response for newly created key - includes the full key only once."""

    key: str
