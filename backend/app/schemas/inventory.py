from typing import Annotated

from pydantic import BaseModel, Field, StrictInt

from ..value_types import INT_MAX, Version
from .cart import Q
from .common import Input


class Restock(Input):
    quantity: Q
    expected_version: Version


class Count(Input):
    counted_available: Annotated[StrictInt, Field(ge=0, le=INT_MAX)]
    expected_version: Version


class InventoryOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    available: int
    pending_occupied: int
    version: str
    updated_at: str


class InventoryMutation(BaseModel):
    product_id: str
    available: int
    version: str
    updated_at: str
    delta: int
