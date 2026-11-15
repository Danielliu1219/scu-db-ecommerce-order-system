from fastapi import APIRouter

from ..dependencies import Actor
from ..schemas.common import Page, Response
from ..schemas.orders import Checkout, OrderOut
from ..services import orders
from ..value_types import ID, OrderStatus
from .common import Paging, response

router = APIRouter(tags=["FR-04/05 订单"])


@router.post(
    "/orders",
    response_model=Response[OrderOut],
    responses={201: {"model": Response[OrderOut]}},
)
def checkout(actor: Actor, data: Checkout):
    result, status = orders.checkout(actor, data)
    return response(result, status)


@router.get("/orders", response_model=Response[Page[OrderOut]])
def listing(
    actor: Actor,
    paging: Paging,
    status: OrderStatus | None = None,
    created_start: str | None = None,
    created_end: str | None = None,
):
    return response(
        orders.listing(
            actor,
            status=status,
            created_start=created_start,
            created_end=created_end,
            page_number=paging.page,
            page_size=paging.page_size,
        )
    )


@router.get("/orders/{order_id}", response_model=Response[OrderOut])
def detail(actor: Actor, order_id: ID):
    return response(orders.detail(actor, order_id))


@router.post("/orders/{order_id}/cancel", response_model=Response[OrderOut])
def cancel(actor: Actor, order_id: ID):
    return response(orders.cancel(actor, order_id))


@router.post("/orders/{order_id}/confirm-receipt", response_model=Response[OrderOut])
def receipt(actor: Actor, order_id: ID):
    return response(orders.advance(actor, order_id))


@router.get("/admin/orders", response_model=Response[Page[OrderOut]])
def admin_listing(
    actor: Actor,
    paging: Paging,
    order_id: ID | None = None,
    user_id: ID | None = None,
    status: OrderStatus | None = None,
    created_start: str | None = None,
    created_end: str | None = None,
):
    return response(
        orders.listing(
            actor,
            True,
            user_id=user_id,
            order_id=order_id,
            status=status,
            created_start=created_start,
            created_end=created_end,
            page_number=paging.page,
            page_size=paging.page_size,
        )
    )


@router.get("/admin/orders/{order_id}", response_model=Response[OrderOut])
def admin_detail(actor: Actor, order_id: ID):
    return response(orders.detail(actor, order_id, True))


@router.post("/admin/orders/{order_id}/ship", response_model=Response[OrderOut])
def ship(actor: Actor, order_id: ID):
    return response(orders.advance(actor, order_id, True))
