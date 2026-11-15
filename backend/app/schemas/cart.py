from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, StrictBool, StrictInt

from ..errors import fail
from ..value_types import ID, INT_MAX
from .common import Input, NonemptyPatch


def quantity(value):
    if isinstance(value, int) and not isinstance(value, bool) and value > INT_MAX:
        fail("QUANTITY_OVERFLOW", 422)
    return value


Q = Annotated[StrictInt, BeforeValidator(quantity), Field(ge=1, le=INT_MAX)]


class CartAdd(Input):
    product_id: ID
    quantity: Q


class CartPatch(NonemptyPatch):
    quantity: Q | None = None
    selected: StrictBool | None = None


class CartItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    price: str
    quantity: int
    selected: bool
    available: int
    status: str
    invalid_reason: str | None


class CartOut(BaseModel):
    id: str
    items: list[CartItemOut]
    selected_total: str


class CartMutation(BaseModel):
    item: CartItemOut
    selected_total: str
