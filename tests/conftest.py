import os

# Configure the environment BEFORE importing the app so the test database and
# JWT secret are used from the very first settings instantiation.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-for-ci")
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select

from Base.db.base import Base
from Base.db.models.user import User
from Base.security.password import hash_password
from main import app


def _bootstrap() -> None:
    sync_engine = create_engine("sqlite:///./test.db", future=True)
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    with sync_engine.begin() as conn:
        # Seed the same demo admin that main.py guarantees on startup, so the
        # /auth/login happy path is exercised regardless of seeding order.
        exists = conn.execute(
            select(User).where(User.username == "admin")
        ).first()
        if not exists:
            conn.execute(
                User.__table__.insert().values(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=hash_password("admin123"),
                    is_active=True,
                )
            )


_bootstrap()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
