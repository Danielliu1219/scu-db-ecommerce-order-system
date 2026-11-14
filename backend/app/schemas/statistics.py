from pydantic import BaseModel

from .common import Page


class MonthlySales(BaseModel):
    sales_month: str
    sales_amount: str
    paid_order_count: int


class TopProduct(BaseModel):
    product_id: str
    product_name: str
    sold_quantity: int


class InactiveUser(BaseModel):
    user_id: str
    username: str
    nickname: str
    phone: str
    created_at: str


class InactivePage(Page[InactiveUser]):
    as_of: str
