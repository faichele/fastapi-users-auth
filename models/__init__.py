"""
Models-Package für das fastapi_users_auth Modul.
"""

from .user_models import (
    User,
    UserBase,
    UserCreate,
    UserUpdate,
    UserPublic,
    UserInDB,
    UserRegister,
    UserLogin,
    UsersPublic,
    UpdatePassword,
    UserUpdateMe
)

from .auth_models import (
    Token,
    TokenData,
    TokenPayload,
    TokenPayloadData,
    NewPassword,
    NewPasswordRequest,
    Message,
    PasswordResetToken,
    LoginResponse
)

__all__ = [
    # User Models
    "User",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserPublic",
    "UserInDB",
    "UserRegister",
    "UserLogin",
    "UsersPublic",
    "UpdatePassword",
    "UserUpdateMe",

    # Auth Models
    "Token",
    "TokenData",
    "TokenPayload",
    "TokenPayloadData",
    "NewPassword",
    "NewPasswordRequest",
    "Message",
    "PasswordResetToken",
    "LoginResponse",
]
