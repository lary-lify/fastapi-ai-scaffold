from __future__ import annotations

from Base.db.models.user import User
from Base.repositories.user_repository import UserRepository
from Base.security.password import hash_password
from Base.services.base import BaseService


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
        """Create a user.

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
        """Public self-registration.

        Validates uniqueness via :meth:`UserRepository.exists` and returns
        ``None`` when the username or email is already taken.
        """
        if await self.repo.exists(username=username) or await self.repo.exists(
            email=email
        ):
            return None
        return await self.repo.create(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
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
