from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import sys
from sqlalchemy import UniqueConstraint

repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))

from fastapi_users_auth.models.group_models import (
    Group,
    GroupCreate,
    GroupPublic,
    UserGroupMembership,
    UserGroupMembershipCreate,
    UserGroupMembershipPublic,
)
from fastapi_users_auth.models.user_models import User


def test_group_models_validate_basic_payloads():
    group = GroupCreate(name="Editors", description="Redaktion", is_active=True)

    assert group.name == "Editors"
    assert group.description == "Redaktion"
    assert group.is_active is True

    public_group = GroupPublic(
        id=uuid4(),
        name="Editors",
        description="Redaktion",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )

    assert public_group.name == "Editors"


def test_membership_models_validate_ids_and_role():
    membership = UserGroupMembershipCreate(
        user_id=uuid4(),
        group_id=uuid4(),
        role="admin",
    )

    assert membership.role == "admin"

    public_membership = UserGroupMembershipPublic(
        id=uuid4(),
        user_id=uuid4(),
        group_id=uuid4(),
        role="member",
        created_at=datetime.now(timezone.utc),
    )

    assert public_membership.role == "member"


def test_group_orm_models_define_relationships_and_constraints():
    assert Group.__tablename__ == "groups"
    assert UserGroupMembership.__tablename__ == "user_group_memberships"
    assert hasattr(User, "group_memberships")
    assert hasattr(User, "groups")
    assert hasattr(Group, "memberships")
    assert hasattr(Group, "users")

    unique_constraints = [
        constraint
        for constraint in UserGroupMembership.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    constrained_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in unique_constraints
    }

    assert ("user_id", "group_id") in constrained_columns
