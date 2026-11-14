from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, model_validator

from ..errors import fail
from ..value_types import ID, OrderStatus, normalize
from .cart import Q
from .common import Input
from .identity import Name, Phone


class CheckoutItem(Input):
    cart_item_id: ID
    quantity: Q


class Checkout(Input):
    checkout_token: str = Field(pattern=r"^[0-9a-f]{32}$")
    items: list[CheckoutItem]
    receiver_name: Name
    receiver_phone: Phone
    receiver_address: Annotated[
        str, BeforeValidator(normalize), Field(min_length=1, max_length=255)
    ]

    @model_validator(mode="after")
    def valid_items(self):
        if not self.items:
            fail("EMPTY_CHECKOUT", 422)
        ids = [item.cart_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate checkout item")
        return self


class PaymentOut(BaseModel):
    payment_id: str
    amount: str
    paid_at: str


class OrderItemOut(BaseModel):
    id: str
    product_id: str
    product_name: str
    unit_price: str
    quantity: int
    line_amount: str


class OrderOut(BaseModel):
    order_id: str
    user_id: str
    username: str
    total_amount: str
    status: OrderStatus
    receiver_name: str
    receiver_phone: str
    receiver_address: str
    created_at: str
    paid_at: str | None
    shipped_at: str | None
    completed_at: str | None
    cancelled_at: str | None
    items: list[OrderItemOut]
    payment: PaymentOut | None
