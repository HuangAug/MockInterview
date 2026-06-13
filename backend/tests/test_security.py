"""Tests for security utilities (T010)."""

import uuid

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

FIXED_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")


class TestPasswordHashing:
    """bcrypt hash/verify with cost=12."""

    def test_hash_produces_bcrypt_string(self) -> None:
        hashed = hash_password("Pass1234")
        assert hashed.startswith("$2b$12$")

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("Pass1234")
        assert verify_password("Pass1234", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("Pass1234")
        assert verify_password("WrongPass1", hashed) is False

    def test_different_hashes_each_time(self) -> None:
        h1 = hash_password("Pass1234")
        h2 = hash_password("Pass1234")
        assert h1 != h2  # bcrypt uses random salt


class TestAccessToken:
    """JWT access token creation and decoding."""

    def test_create_returns_string(self) -> None:
        token = create_access_token(FIXED_UUID)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_returns_user_id(self) -> None:
        token = create_access_token(FIXED_UUID)
        decoded_id = decode_access_token(token)
        assert decoded_id == FIXED_UUID

    def test_decode_invalid_token_raises_40101(self) -> None:
        from app.core.exceptions import AppException

        with pytest.raises(AppException) as exc_info:
            decode_access_token("invalid.token.string")
        assert exc_info.value.code == 40101

    def test_decode_tampered_token_raises_40101(self) -> None:
        from app.core.exceptions import AppException

        token = create_access_token(FIXED_UUID)
        tampered = token[:-4] + "xxxx"
        with pytest.raises(AppException) as exc_info:
            decode_access_token(tampered)
        assert exc_info.value.code == 40101

    def test_token_contains_standard_claims(self) -> None:
        from jose import jwt

        from app.core.config import settings

        token = create_access_token(FIXED_UUID)
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["sub"] == str(FIXED_UUID)


class TestRefreshToken:
    """Refresh token generation and hashing."""

    def test_create_returns_128_hex_chars(self) -> None:
        token = create_refresh_token()
        assert len(token) == 128
        assert all(c in "0123456789abcdef" for c in token)

    def test_create_produces_unique_tokens(self) -> None:
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert t1 != t2

    def test_hash_returns_sha256_hex(self) -> None:
        token = create_refresh_token()
        hashed = hash_refresh_token(token)
        assert len(hashed) == 64  # SHA-256 = 32 bytes = 64 hex chars
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_hash_is_deterministic(self) -> None:
        token = "abc123" * 20
        assert hash_refresh_token(token) == hash_refresh_token(token)

    def test_different_tokens_different_hashes(self) -> None:
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert hash_refresh_token(t1) != hash_refresh_token(t2)
