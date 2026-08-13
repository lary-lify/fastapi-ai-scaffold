import os

# Configure the environment BEFORE importing the app so the test database and
# JWT secret are used from the very first settings instantiation.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-for-ci")
os.environ.setdefault("APP_ENV", "test")

from sqlalchemy import create_engine, select

from app.db.base import Base
from app.db.models.user import User
from app.security.password import hash_password


def _bootstrap() -> None:
    sync_engine = create_engine("sqlite:///./test.db", future=True)
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    with sync_engine.begin() as conn:
        exists = conn.execute(
            select(User).where(User.username == "tester")
        ).first()
        if not exists:
            conn.execute(
                User.__table__.insert().values(
                    username="tester",
                    email="tester@example.com",
                    hashed_password=hash_password("tester123"),
                    is_active=True,
                )
            )


_bootstrap()
