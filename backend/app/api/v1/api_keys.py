import uuid

import structlog
from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbDep
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from app.services.api_key_service import create_api_key, list_api_keys, revoke_api_key

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyResponse])
async def list_keys(current_user: CurrentUser, db: DbDep) -> list[ApiKeyResponse]:
    keys = await list_api_keys(db, current_user.id)
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_key(
    payload: ApiKeyCreate, current_user: CurrentUser, db: DbDep
) -> ApiKeyCreatedResponse:
    api_key, plain_key = await create_api_key(
        db,
        user_id=current_user.id,
        name=payload.name,
        rate_limit=payload.rate_limit,
    )
    base = ApiKeyResponse.model_validate(api_key)
    return ApiKeyCreatedResponse(**base.model_dump(), key=plain_key)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(key_id: uuid.UUID, current_user: CurrentUser, db: DbDep) -> None:
    revoked = await revoke_api_key(db, key_id=key_id, user_id=current_user.id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
