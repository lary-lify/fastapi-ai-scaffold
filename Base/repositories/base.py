from typing import Any, Generic, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Generic async CRUD repository for a single ORM model.

    Subclasses set ``model`` to the concrete ORM class::

        class UserRepository(BaseRepository[User]):
            model = User

    The generic helpers cover the 90% case; override any method for custom
    behaviour.
    """

    model: Type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: Any) -> ModelType | None:
        return await self.session.get(self.model, obj_id)

    async def list(self, **filters: Any) -> list[ModelType]:
        stmt = select(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        if hasattr(self.model, "id"):
            stmt = stmt.order_by(self.model.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        for field, value in kwargs.items():
            setattr(obj, field, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        await self.session.delete(obj)
        await self.session.commit()

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())
