from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

DataType = TypeVar("DataType")


class BaseSchema(BaseModel):
    """Pydantic base that reads ORM attributes by default."""

    model_config = ConfigDict(from_attributes=True)


class PageSchema(BaseSchema, Generic[DataType]):
    """Generic pagination envelope."""

    total: int
    page: int
    page_size: int
    items: list[DataType]
