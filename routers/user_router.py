"""
User Router für das fastapi_users_auth Modul mit Multi-Provider-Unterstützung.

Dieser Router behandelt alle benutzerverwaltungsbezogenen Endpunkte:
- Benutzer-CRUD-Operationen
- Profilverwaltung
- Passwort-Updates
- Admin-Funktionen
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.user_models import (
    User, UserCreate, UserUpdate,
    UserUpdateMe, UserPublic,
    UsersPublic, UpdatePassword)
from ..models.auth_models import Message
from ..services.base_user_service import BaseUserService

from ..dependencies.auth_deps import (
    AuthDependencies,
    get_current_user as get_current_user_provider,
    get_current_active_user as get_current_active_user_provider,
    get_current_active_superuser as get_current_active_superuser_provider,
)


# --- Freie Routen-Handler-Funktionen ---
def get_users(
    user_service: BaseUserService,
    current_user: User,
    skip: int = Query(default=0, ge=0, description="Anzahl zu überspringender Datensätze"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximale Anzahl Datensätze"),
    search: str | None = Query(default=None, description="Suchbegriff für E-Mail oder Name"),
    is_active: bool | None = Query(default=None, description="Filter für aktive Benutzer"),
) -> UsersPublic:
    """Holt eine Liste von Benutzern (nur für Superuser)."""
    users, total_count = user_service.get_users(
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
    )
    return UsersPublic(
        data=[UserPublic.model_validate(user) for user in users],
        count=total_count,
    )


def create_user(
    user_create: UserCreate,
    user_service: BaseUserService,
    current_user: User,
) -> UserPublic:
    """Erstellt einen neuen Benutzer (nur für Superuser)."""
    try:
        user = user_service.create_user(user_create)
        return UserPublic.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def get_current_user(
    current_user: User,
) -> UserPublic:
    """Holt die Informationen des aktuell angemeldeten Benutzers."""
    return UserPublic.model_validate(current_user)


def update_current_user(
    user_update: UserUpdateMe,
    user_service: BaseUserService,
    current_user: User,
) -> UserPublic:
    """Aktualisiert die eigenen Benutzerdaten."""
    try:
        updated_user = user_service.update_user_me(current_user.id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserPublic.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def update_current_user_password(
    password_update: UpdatePassword,
    user_service: BaseUserService,
    current_user: User,
) -> Message:
    """Aktualisiert das eigene Passwort."""
    try:
        success = user_service.update_password(current_user.id, password_update)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return Message(message="Passwort erfolgreich aktualisiert")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def get_user_by_id(
    user_id: UUID,
    user_service: BaseUserService,
    current_user: User,
) -> UserPublic:
    """Holt einen Benutzer anhand der ID (nur eigene Daten oder als Superuser)."""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user",
        )

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserPublic.model_validate(user)


def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    user_service: BaseUserService,
    current_user: User,
) -> UserPublic:
    """Aktualisiert einen Benutzer (nur für Superuser)."""
    try:
        updated_user = user_service.update_user(user_id, user_update)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserPublic.model_validate(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


def delete_user(
    user_id: UUID,
    user_service: BaseUserService,
    current_user: User,
) -> Message:
    """Löscht einen Benutzer (nur für Superuser)."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    success = user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return Message(message="User successfully deleted")


def deactivate_user(
    user_id: UUID,
    user_service: BaseUserService,
    current_user: User,
) -> UserPublic:
    """Deaktiviert einen Benutzer (nur für Superuser)."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    user = user_service.deactivate_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserPublic.model_validate(user)


def activate_user(
    user_id: UUID,
    user_service: BaseUserService,
    current_user: User,
) -> UserPublic:
    """Aktiviert einen Benutzer (nur für Superuser)."""
    user = user_service.activate_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserPublic.model_validate(user)


def check_email_availability(
    email: str,
    user_service: BaseUserService,
    current_user: User,
    exclude_user_id: UUID | None = Query(default=None, description="Benutzer-ID zum Ausschließen"),
) -> dict[str, bool]:
    """Prüft, ob eine E-Mail-Adresse verfügbar ist."""
    if not current_user.is_superuser:
        if exclude_user_id and exclude_user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only check availability for your own email",
            )
        exclude_user_id = current_user.id

    is_available = user_service.is_email_available(email, exclude_user_id)
    return {"available": is_available}


def create_user_router(
    user_service: BaseUserService,
    auth_deps: AuthDependencies,
    prefix: str = "/users",
) -> APIRouter:
    """Erzeugt einen APIRouter mit freien Handler-Funktionen und korrekt gebundenen Dependencies."""

    # Konkrete Dependency-Funktionen im Closure definieren
    def get_user_service_dep() -> BaseUserService:
        return user_service

    # Korrekt gebundene Dependency-Funktionen
    get_current_user_dep = get_current_user_provider(auth_deps)
    get_current_active_user_dep = get_current_active_user_provider(auth_deps)
    get_current_superuser_dep = get_current_active_superuser_provider(auth_deps)


    # Lokale Aliase für die Annotated-Typen mit den echten Dependencies
    LocalUserServiceDep = Annotated[BaseUserService, Depends(get_user_service_dep)]
    LocalCurrentUserDep = Annotated[User, Depends(get_current_user_dep)]
    LocalCurrentActiveUserDep = Annotated[User, Depends(get_current_active_user_dep)]
    LocalCurrentSuperuserDep = Annotated[User, Depends(get_current_superuser_dep)]

    # Wrapper-Funktionen, die die generischen Handler mit konkreten Dependencies verbinden

    def _get_users(
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentSuperuserDep,
        skip: int = Query(default=0, ge=0, description="Anzahl zu überspringender Datensätze"),
        limit: int = Query(default=100, ge=1, le=1000, description="Maximale Anzahl Datensätze"),
        search: str | None = Query(default=None, description="Suchbegriff für E-Mail oder Name"),
        is_active: bool | None = Query(default=None, description="Filter für aktive Benutzer"),
    ) -> UsersPublic:
        return get_users(user_service, current_user, skip, limit, search, is_active)

    def _create_user(
        user_create: UserCreate,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentSuperuserDep,
    ) -> UserPublic:
        return create_user(user_create, user_service, current_user)

    def _get_current_user(
        current_user: LocalCurrentActiveUserDep,
    ) -> UserPublic:
        return get_current_user(current_user)

    def _update_current_user(
        user_update: UserUpdateMe,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentActiveUserDep,
    ) -> UserPublic:
        return update_current_user(user_update, user_service, current_user)

    def _update_current_user_password(
        password_update: UpdatePassword,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentActiveUserDep,
    ) -> Message:
        return update_current_user_password(password_update, user_service, current_user)

    def _get_user_by_id(
        user_id: UUID,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentActiveUserDep,
    ) -> UserPublic:
        return get_user_by_id(user_id, user_service, current_user)

    def _update_user(
        user_id: UUID,
        user_update: UserUpdate,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentSuperuserDep,
    ) -> UserPublic:
        return update_user(user_id, user_update, user_service, current_user)

    def _delete_user(
        user_id: UUID,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentSuperuserDep,
    ) -> Message:
        return delete_user(user_id, user_service, current_user)

    def _deactivate_user(
        user_id: UUID,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentSuperuserDep,
    ) -> UserPublic:
        return deactivate_user(user_id, user_service, current_user)

    def _activate_user(
        user_id: UUID,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentSuperuserDep,
    ) -> UserPublic:
        return activate_user(user_id, user_service, current_user)

    def _check_email_availability(
        email: str,
        user_service: LocalUserServiceDep,
        current_user: LocalCurrentActiveUserDep,
        exclude_user_id: UUID | None = Query(default=None, description="Benutzer-ID zum Ausschließen"),
    ) -> dict[str, bool]:
        return check_email_availability(email, user_service, current_user, exclude_user_id)

    router = APIRouter(prefix=prefix, tags=["users"])

    router.get("/", response_model=UsersPublic)(_get_users)
    router.post("/", response_model=UserPublic)(_create_user)
    router.get("/me", response_model=UserPublic)(_get_current_user)
    router.patch("/me", response_model=UserPublic)(_update_current_user)
    router.patch("/me/password", response_model=Message)(_update_current_user_password)
    router.get("/{user_id}", response_model=UserPublic)(_get_user_by_id)
    router.patch("/{user_id}", response_model=UserPublic)(_update_user)
    router.delete("/{user_id}", response_model=Message)(_delete_user)
    router.patch("/{user_id}/deactivate", response_model=UserPublic)(_deactivate_user)
    router.patch("/{user_id}/activate", response_model=UserPublic)(_activate_user)
    router.get("/email/{email}/available", response_model=dict)(_check_email_availability)

    return router


class UserRouter:
    """
    Kompatibilitäts-Wrapper für UserRouter.

    Diese Klasse dient als Adapter für bestehende Importe und delegiert
    die eigentliche Router-Erstellung an die create_user_router Factory-Funktion.
    """

    def __init__(
            self,
            user_service: BaseUserService,
            auth_deps: AuthDependencies,
            prefix: str = "/users",
    ):
        """
        Initialisiert den UserRouter-Wrapper.

        Args:
            user_service: Der Benutzerservice für die Geschäftslogik
            auth_deps: Die Auth-Dependencies für die Authentifizierung
            prefix: Das URL-Präfix für die User-Routen
        """
        self.user_service = user_service
        self.auth_deps = auth_deps
        self.prefix = prefix
        self._router: APIRouter | None = None

    @property
    def router(self) -> APIRouter:
        """Gibt den APIRouter zurück (lazy initialization)."""
        if self._router is None:
            self._router = create_user_router(
                user_service=self.user_service,
                auth_deps=self.auth_deps,
                prefix=self.prefix,
            )
        return self._router
