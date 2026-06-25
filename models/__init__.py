"""
Models-Package für das fastapi_users_auth Modul.
"""

from ..model_factory import AuthORMModels, create_auth_models, configure_auth_models

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
    UserUpdateMe,
    UserRole,
    Language
)

from .group_models import (
    Group,
    UserGroupMembership,
    GroupBase,
    GroupCreate,
    GroupUpdate,
    GroupInDB,
    GroupPublic,
    GroupsPublic,
    UserGroupMembershipBase,
    UserGroupMembershipCreate,
    UserGroupMembershipUpdate,
    UserGroupMembershipInDB,
    UserGroupMembershipPublic,
    UserGroupMembershipsPublic,
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
    LoginResponse,
    TwoFactorAuthSecret,
    TwoFactorAuthentication,
    TwoFactorAuthVerificationCode,
    UserAlert
)

__all__ = [
    # Factory
    "AuthORMModels",
    "create_auth_models",
    "configure_auth_models",

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
    "UserRole",
    "Language"

    # Group Models
    "Group",
    "UserGroupMembership",
    "GroupBase",
    "GroupCreate",
    "GroupUpdate",
    "GroupInDB",
    "GroupPublic",
    "GroupsPublic",
    "UserGroupMembershipBase",
    "UserGroupMembershipCreate",
    "UserGroupMembershipUpdate",
    "UserGroupMembershipInDB",
    "UserGroupMembershipPublic",
    "UserGroupMembershipsPublic",

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
    "TwoFactorAuthSecret",
    "TwoFactorAuthentication",
    "TwoFactorAuthVerificationCode",
    "UserAlert"
]
