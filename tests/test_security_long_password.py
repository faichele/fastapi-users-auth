import pytest

from fastapi_users_auth.utils.security import SecurityUtils


def test_default_hash_uses_argon2() -> None:
    security = SecurityUtils()

    hashed = security.get_password_hash("correct-password")

    assert hashed.startswith("$argon2")


def test_bcrypt_hashes_remain_accepted() -> None:
    legacy_security = SecurityUtils(schemes=["bcrypt"])
    security = SecurityUtils()

    password = "correct-password"
    bcrypt_hash = legacy_security.get_password_hash(password)

    assert security.verify_password(password, bcrypt_hash) is True


def test_argon2_allows_long_password_roundtrip() -> None:
    security = SecurityUtils(schemes=["argon2"])

    long_password = "a" * 200
    hashed = security.get_password_hash(long_password)

    assert security.verify_password(long_password, hashed) is True


def test_wrong_password_is_rejected() -> None:
    security = SecurityUtils(schemes=["argon2"])

    hashed = security.get_password_hash("correct-password")

    assert security.verify_password("wrong-password", hashed) is False
