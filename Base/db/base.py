from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from Base.config.setting import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine: AsyncEngine = create_async_engine(
    settings.database.url,
    echo=settings.database.echo,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async session."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables from metadata. Dev convenience only.

    Production should use Alembic migrations (``make db-upgrade``); this keeps
    local zero-config runs working without a migration step.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
