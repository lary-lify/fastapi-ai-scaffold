from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone

from Base.clients.email import get_email_client
from Base.config.setting import settings
from Base.db.models.user import User
from Base.repositories.user_repository import UserRepository
from Base.security.password import hash_password
from Base.services.base import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    """Business logic for users (delegates persistence to UserRepository)."""

    def __init__(self, session):
        super().__init__(session)
        self.repo = UserRepository(session)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.repo.get_by_id(user_id)

    async def list(self) -> list[User]:
        return await self.repo.list()

    async def create(self, *, username: str, email: str, password: str) -> User | None:
        """Create a user (admin path).

        Returns ``None`` when the username or email already exists.
        """
        if (
            await self.repo.count(username=username) > 0
            or await self.repo.count(email=email) > 0
        ):
            return None
        return await self.repo.create(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
        )

    async def register(self, *, username: str, email: str, password: str) -> User | None:
        """Public self-registration with email verification.

        Validates uniqueness via :meth:`UserRepository.exists`, mints a
        single-use verification token, then fires the verification email.
        Returns ``None`` when the username or email is already taken.
        """
        if await self.repo.exists(username=username) or await self.repo.exists(
            email=email
        ):
            return None
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(
            hours=settings.email.token_expire_hours
        )
        user = await self.repo.create(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            is_verified=False,
            verification_token=token,
            verification_token_expires_at=expires,
        )
        await self._send_verification_email(user)
        return user

    async def _send_verification_email(self, user: User) -> None:
        link = (
            f"{settings.app.base_url.rstrip('/')}"
            f"/auth/verify-email?token={user.verification_token}"
        )
        subject = "请验证你的邮箱"
        body = (
            f"你好 {user.username}，\n\n"
            f"感谢注册。请点击以下链接完成邮箱验证"
            f"（{settings.email.token_expire_hours} 小时内有效）：\n{link}\n\n"
            f"如果此邮件非你本人请求，请直接忽略。"
        )
        try:
            await get_email_client().send(to=user.email, subject=subject, body=body)
        except Exception:  # backend failure must not break registration
            logger.exception("发送验证邮件失败 to=%s", user.email)

    async def verify_email(self, token: str) -> User | None:
        """Activate the account behind ``token``.

        Returns the updated user, or ``None`` when the token is missing,
        unknown, or expired.
        """
        user = await self.repo.get_by_verification_token(token)
        if user is None or user.verification_token_expires_at is None:
            return None
        expires_at = user.verification_token_expires_at
        # SQLite stores naive UTC; coerce so comparisons stay tz-consistent.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None
        return await self.repo.update(
            user,
            is_verified=True,
            verification_token=None,
            verification_token_expires_at=None,
        )

    async def paginate(
        self, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[User], int]:
        """Return a paginated ``(users, total)`` slice delegated to the repo."""
        return await self.repo.paginate(page=page, page_size=page_size)

    async def update(self, user: User, **kwargs) -> User:
        """Update a user. Supports a plaintext ``password`` kwarg."""
        password = kwargs.pop("password", None)
        if password:
            kwargs["hashed_password"] = hash_password(password)
        return await self.repo.update(user, **kwargs)

    async def delete(self, user: User) -> None:
        await self.repo.delete(user)
