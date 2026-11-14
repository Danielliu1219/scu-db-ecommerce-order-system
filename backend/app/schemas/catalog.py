from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from ..value_types import ID, ProductStatus, money, normalize
from .common import Input, NonemptyPatch

CategoryName = Annotated[str, BeforeValidator(normalize), Field(min_length=1, max_length=50)]
ProductName = Annotated[str, BeforeValidator(normalize), Field(min_length=1, max_length=100)]
Price = Annotated[Decimal, BeforeValidator(money)]


class CategoryInput(Input):
    name: CategoryName


class ProductCreate(Input):
    category_id: ID
    name: ProductName
    price: Price
    description: str = Field(max_length=16000)
    status: ProductStatus = "OFF_SHELF"


class ProductPatch(NonemptyPatch):
    category_id: ID | None = None
    name: ProductName | None = None
    price: Price | None = None
    description: str | None = Field(None, max_length=16000)


class StatusInput(Input):
    status: ProductStatus


class CategoryOut(BaseModel):
    id: str
    name: str


class ProductOut(BaseModel):
    id: str
    category_id: str
    category_name: str
    name: str
    price: str
    description: str
    status: ProductStatus
    available: int
    created_at: str
    updated_at: str
