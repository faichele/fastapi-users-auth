import pytest

from fastapi_users_auth.utils.security import SecurityUtils


def test_argon2_allows_long_password_roundtrip() -> None:
    security = SecurityUtils(schemes=["argon2"])

    long_password = "a" * 200
    hashed = security.get_password_hash(long_password)

    assert security.verify_password(long_password, hashed) is True


def test_wrong_password_is_rejected() -> None:
    security = SecurityUtils(schemes=["argon2"])

    hashed = security.get_password_hash("correct-password")

    assert security.verify_password("wrong-password", hashed) is False
