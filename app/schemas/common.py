from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)


class PaginatedResponse(GenericModel, Generic[T]):
    data: List[T]
    meta: PaginationMeta