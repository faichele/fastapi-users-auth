from uuid import UUID, uuid4

import sqlalchemy as sa
from fastapi_users_auth import configure_auth_models, create_auth_models
from fastapi_users_auth.models import group_models, user_models
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, declarative_base


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


def test_user_id_override_controls_foreign_key_types():
    TestBase = declarative_base()
    string_models = create_auth_models(
        TestBase,
        table_prefix="tenant_",
        user_attrs_override={
            "id": sa.Column(sa.String(36), primary_key=True),
        },
    )

    assert string_models.User.__table__.c.id.type.python_type is str
    assert string_models.UserSession.__table__.c.user_id.type.python_type is str
    assert string_models.UserGroupMembership.__table__.c.user_id.type.python_type is str


def test_default_id_columns_compile_as_postgresql_uuid():
    models = create_auth_models(declarative_base())
    columns = [
        models.User.__table__.c.id,
        models.Group.__table__.c.id,
        models.UserGroupMembership.__table__.c.id,
        models.UserGroupMembership.__table__.c.user_id,
        models.UserGroupMembership.__table__.c.group_id,
        models.UserSession.__table__.c.user_id,
    ]
    for column in columns:
        assert column.type.python_type is UUID
        assert column.type.compile(dialect=postgresql.dialect()) == "UUID"
    assert {"department", "language", "two_fa_enabled"} <= set(models.User.__table__.c.keys())


def test_session_user_id_and_user_uuid_share_one_persisted_column():
    base = declarative_base()
    models = create_auth_models(base, table_prefix="session_")
    assert "user_id" in models.UserSession.__table__.c
    assert "user_uuid" not in models.UserSession.__table__.c
    engine = sa.create_engine("sqlite://")
    base.metadata.create_all(engine)

    with Session(engine) as db:
        user = models.User(id=uuid4(), email="user@example.com", hashed_password="hash")
        db.add(user)
        db.flush()
        db.add_all([
            models.UserSession(user_id=user.id),
            models.UserSession(user_uuid=user.id),
        ])
        db.commit()
        sessions = db.query(models.UserSession).filter(models.UserSession.user_uuid == user.id).all()
        assert len(sessions) == 2
        assert all(session.user_id == session.user_uuid == user.id for session in sessions)
        assert all(session.user.id == user.id for session in sessions)
    engine.dispose()


def test_configure_auth_models_rebinds_public_orm_aliases():
    TestBase = declarative_base()
    SharedBase = declarative_base()
    default_models = create_auth_models(SharedBase)

    try:
        configured_models = configure_auth_models(TestBase, table_prefix="app_")

        assert user_models.User is configured_models.User
        assert group_models.Group is configured_models.Group
        assert group_models.UserGroupMembership is configured_models.UserGroupMembership
        assert configured_models.User.__tablename__ == "app_users"
    finally:
        configure_auth_models(SharedBase, table_prefix=default_models.table_prefix)

