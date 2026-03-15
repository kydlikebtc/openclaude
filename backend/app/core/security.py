import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        subject: str | None = payload.get("sub")
        return subject
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure random API key with oc_ prefix."""
    return f"oc_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """Hash an API key for storage (non-reversible)."""
    return pwd_context.hash(key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    return pwd_context.verify(plain_key, hashed_key)
