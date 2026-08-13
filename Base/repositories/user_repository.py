from Base.db.models.user import User
from Base.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """CRUD repository for the :class:`User` model."""

    model = User
