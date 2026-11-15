from fastapi import APIRouter

from ..dependencies import Actor
from ..schemas.common import Page, Response
from ..schemas.inventory import Count, InventoryMutation, InventoryOut, Restock
from ..services import inventory
from ..value_types import ID
from .common import Paging, response

router = APIRouter(tags=["FR-08 库存"])


@router.get("/admin/inventory", response_model=Response[Page[InventoryOut]])
def listing(
    actor: Actor,
    paging: Paging,
    product_id: ID | None = None,
    keyword: str | None = None,
):
    return response(inventory.listing(actor, product_id, keyword, paging.page, paging.page_size))


@router.post("/admin/inventory/{product_id}/restock", response_model=Response[InventoryMutation])
def restock(actor: Actor, product_id: ID, data: Restock):
    return response(inventory.maintain(actor, product_id, data))


@router.post("/admin/inventory/{product_id}/count", response_model=Response[InventoryMutation])
def count(actor: Actor, product_id: ID, data: Count):
    return response(inventory.maintain(actor, product_id, data, True))
