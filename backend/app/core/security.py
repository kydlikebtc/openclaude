import base64
import os
import secrets
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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


def _get_aes_key() -> bytes:
    """Derive a 32-byte AES key from the configured hex string."""
    hex_key = settings.redis_encryption_key
    try:
        key_bytes = bytes.fromhex(hex_key)
    except ValueError:
        # If not valid hex, use SHA-256 of the raw string as fallback
        import hashlib
        key_bytes = hashlib.sha256(hex_key.encode()).digest()
    # Pad or truncate to 32 bytes for AES-256
    return (key_bytes + b"\x00" * 32)[:32]


def encrypt_for_redis(plaintext: str) -> str:
    """Encrypt a plaintext string using AES-256-GCM for Redis storage.

    Returns a base64url-encoded string: nonce(12) + ciphertext + tag(16).
    Use decrypt_from_redis() to reverse.
    """
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt_from_redis(encrypted: str) -> str:
    """Decrypt an AES-256-GCM encrypted value from Redis.

    Raises ValueError if decryption fails (wrong key or tampered data).
    """
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(encrypted.encode())
    nonce = raw[:12]
    ciphertext = raw[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()
