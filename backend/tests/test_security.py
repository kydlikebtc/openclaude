import pytest
from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_api_key,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    password = "mysecurepassword"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_generate_api_key_format() -> None:
    key = generate_api_key()
    assert key.startswith("oc_")
    assert len(key) > 20


def test_generate_api_key_unique() -> None:
    keys = {generate_api_key() for _ in range(100)}
    assert len(keys) == 100  # All unique


def test_create_and_decode_token() -> None:
    subject = "user-uuid-123"
    token = create_access_token(subject)
    decoded = decode_access_token(token)
    assert decoded == subject


def test_decode_expired_token() -> None:
    token = create_access_token("user-123", expires_delta=timedelta(seconds=-1))
    decoded = decode_access_token(token)
    assert decoded is None


def test_decode_invalid_token() -> None:
    decoded = decode_access_token("not.a.valid.token")
    assert decoded is None
