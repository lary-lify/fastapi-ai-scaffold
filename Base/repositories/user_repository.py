from sqlalchemy import select

from Base.db.models.user import User
from Base.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """CRUD repository for the :class:`User` model."""

    model = User

    async def get_by_verification_token(self, token: str) -> User | None:
        """Return the user owning ``token``, or ``None`` if not found."""
        result = await self.session.execute(
            select(User).where(User.verification_token == token)
        )
        return result.scalar_one_or_none()
