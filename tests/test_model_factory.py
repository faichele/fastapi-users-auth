from pathlib import Path
from importlib import import_module

import sys
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

repo_root = Path(__file__).resolve().parents[3]
packages_root = repo_root / "packages"
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(packages_root))

SharedBase = import_module("packages.fastapi_shared_orm").Base
fastapi_users_auth = import_module("packages.fastapi_users_auth")
create_auth_models = fastapi_users_auth.create_auth_models
configure_auth_models = fastapi_users_auth.configure_auth_models
group_models = import_module("packages.fastapi_users_auth.models.group_models")
user_models = import_module("packages.fastapi_users_auth.models.user_models")


def test_create_auth_models_builds_prefixed_tables_and_caches_per_base_prefix():
    TestBase = declarative_base()

    models = create_auth_models(TestBase, table_prefix="tenant_")
    same_models = create_auth_models(TestBase, table_prefix="tenant_")
    other_models = create_auth_models(TestBase, table_prefix="audit_")

    assert models is same_models
    assert models.User is same_models.User
    assert other_models.User is not models.User

    assert models.user_table_name == "tenant_users"
    assert models.group_table_name == "tenant_groups"
    assert models.membership_table_name == "tenant_user_group_memberships"
    assert models.User.__tablename__ == "tenant_users"
    assert models.Group.__tablename__ == "tenant_groups"
    assert models.UserGroupMembership.__tablename__ == "tenant_user_group_memberships"

    user_fk = next(iter(models.UserGroupMembership.__table__.c.user_id.foreign_keys))
    group_fk = next(iter(models.UserGroupMembership.__table__.c.group_id.foreign_keys))

    assert user_fk.target_fullname == "tenant_users.id"
    assert group_fk.target_fullname == "tenant_groups.id"
    assert hasattr(models.User, "group_memberships")
    assert hasattr(models.User, "groups")
    assert hasattr(models.Group, "memberships")
    assert hasattr(models.Group, "users")


def test_create_auth_models_uses_separate_cache_entries_for_different_user_id_types():
    TestBase = declarative_base()
    UuidBase = declarative_base()

    create_auth_models(TestBase, table_prefix="tenant_")
    uuid_models = create_auth_models(
        UuidBase,
        table_prefix="tenant_",
        user_attrs_override={
            "id": sa.Column(sa.UUID(as_uuid=True), primary_key=True, index=True, default=sa.text("gen_random_uuid()")),
        },
    )

    assert type(uuid_models.UserSession.__table__.c.user_uuid.type) is type(uuid_models.User.__table__.c.id.type)
    assert type(uuid_models.UserGroupMembership.__table__.c.user_id.type) is type(uuid_models.User.__table__.c.id.type)
    assert uuid_models.User.__table__.c.id.type.python_type is UUID
    assert uuid_models.UserSession.__table__.c.user_uuid.type.python_type is UUID
    assert uuid_models.UserGroupMembership.__table__.c.user_id.type.python_type is UUID


def test_configure_auth_models_rebinds_public_orm_aliases():
    TestBase = declarative_base()
    default_models = create_auth_models(SharedBase)

    try:
        configured_models = configure_auth_models(TestBase, table_prefix="app_")

        assert user_models.User is configured_models.User
        assert group_models.Group is configured_models.Group
        assert group_models.UserGroupMembership is configured_models.UserGroupMembership
        assert configured_models.User.__tablename__ == "app_users"
    finally:
        configure_auth_models(SharedBase, table_prefix=default_models.table_prefix)

