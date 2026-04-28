"""Legacy-Exports für Abwärtskompatibilität.

Historisch wurden in diesem Modul Pydantic- und (teilweise fehlerhafte)
SQLAlchemy-Modelle gemischt. Für den gemeinsamen ORM-Core liegen die echten
SQLAlchemy-Tabellen jetzt in:
- `packages.fastapi_users_auth.models.user_models` (User)
- `packages.fastapi_users_auth.models.group_models` (Groups, Memberships)

Token/Reset-Modelle sind Pydantic-Schemas in:
- `packages.fastapi_users_auth.models.auth_models`

Bitte neue Imports bevorzugt aus diesen Modulen beziehen.
"""

from packages.fastapi_users_auth.model_factory import (
    AuthORMModels,
    create_auth_models,
    configure_auth_models,
)
from packages.fastapi_users_auth.models.user_models import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserPublic,
    UsersPublic,
    UserLogin,
    UserRegister,
    UserUpdateMe,
    UpdatePassword,
)

from packages.fastapi_users_auth.models.group_models import (
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

from packages.fastapi_users_auth.models.auth_models import (
    Token,
    TokenData,
    TokenPayload,
    TokenPayloadData,
    NewPassword,
    NewPasswordRequest,
    Message,
)

__all__ = [
    "AuthORMModels",
    "create_auth_models",
    "configure_auth_models",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserPublic",
    "UsersPublic",
    "UserLogin",
    "UserRegister",
    "UserUpdateMe",
    "UpdatePassword",
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
    "Token",
    "TokenData",
    "TokenPayload",
    "TokenPayloadData",
    "NewPassword",
    "NewPasswordRequest",
    "Message",
]
