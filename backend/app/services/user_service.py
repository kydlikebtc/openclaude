import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User

logger = structlog.get_logger(__name__)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    logger.info("Creating user", email=email)
    user = User(
        email=email,
        password_hash=hash_password(password),
        status="active",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("User created", user_id=str(user.id), email=email)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user:
        logger.info("Authentication failed: user not found", email=email)
        return None
    if not verify_password(password, user.password_hash):
        logger.info("Authentication failed: wrong password", email=email)
        return None
    if user.status != "active":
        logger.info("Authentication failed: user inactive", email=email, status=user.status)
        return None
    return user
