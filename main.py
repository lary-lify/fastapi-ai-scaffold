from app.config.log import setup_logging

setup_logging()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.common.exceptions import register_exception_handlers
from app.config.setting import settings
from app.db.base import SessionLocal, init_db
from app.db.models.user import User
from app.middleware.request_log import RequestLogMiddleware
from app.routers import auth, health, users
from app.security.password import hash_password

logger = logging.getLogger(__name__)

DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin123"


async def _seed_demo_user() -> None:
    """Create a demo admin on first boot so /auth/login is usable out of the box."""
    async with SessionLocal() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalars().first() is None:
            db.add(
                User(
                    username=DEMO_USERNAME,
                    email="admin@example.com",
                    hashed_password=hash_password(DEMO_PASSWORD),
                )
            )
            await db.commit()
            logger.info("Seeded demo admin user: %s / %s", DEMO_USERNAME, DEMO_PASSWORD)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast in production if the JWT secret is still the placeholder.
    if settings.app.env == "prod" and settings.auth.jwt_secret == "change-me-in-production":
        raise RuntimeError("Refusing to start in prod with placeholder JWT_SECRET")

    await init_db()
    await _seed_demo_user()
    logger.info("Application started (env=%s)", settings.app.env)
    yield
    logger.info("Application shut down")


app = FastAPI(title=settings.app.name, lifespan=lifespan)

# CORS: explicit origins only. Never combine "*" with allow_credentials=True.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLogMiddleware)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
