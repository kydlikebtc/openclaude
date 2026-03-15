import uuid
from typing import Annotated

import structlog
from fastapi import Cookie, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import AsyncSession, get_db
from app.core.security import decode_access_token
from app.models.miner import Miner
from app.models.user import User
from app.services.miner_service import get_miner_by_id
from app.services.user_service import get_user_by_id

logger = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    # Prefer explicit Bearer header (API clients); fall back to httpOnly cookie (browsers)
    token = (credentials.credentials if credentials else None) or access_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_id(db, user_id)
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_miner(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)],
) -> Miner:
    """Extract and validate a miner JWT.  Subject format: 'miner:<uuid>'."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    subject = decode_access_token(credentials.credentials)
    if not subject or not subject.startswith("miner:"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired miner token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        miner_id = uuid.UUID(subject.removeprefix("miner:"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed miner token subject",
        )
    miner = await get_miner_by_id(db, miner_id)
    if not miner or miner.status not in ("active", "registered"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Miner not found or inactive",
        )
    logger.debug("miner authenticated", miner_id=str(miner_id))
    return miner


async def get_admin_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Require authenticated user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentMiner = Annotated[Miner, Depends(get_current_miner)]
AdminUser = Annotated[User, Depends(get_admin_user)]
