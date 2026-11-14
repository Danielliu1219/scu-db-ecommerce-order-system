from fastapi import APIRouter
from fastapi import Response as EmptyResponse

from ..dependencies import Actor
from ..schemas.cart import CartAdd, CartMutation, CartOut, CartPatch
from ..schemas.common import Response
from ..services import cart
from ..value_types import ID
from .common import response

router = APIRouter(tags=["FR-03 购物车"])


@router.get("/cart", response_model=Response[CartOut])
def listing(actor: Actor):
    return response(cart.listing(actor))


@router.post(
    "/cart/items",
    response_model=Response[CartMutation],
    responses={201: {"model": Response[CartMutation]}},
)
def add(actor: Actor, data: CartAdd):
    result, status = cart.add(actor, data)
    return response(result, status)


@router.patch("/cart/items/{item_id}", response_model=Response[CartMutation])
def edit(actor: Actor, item_id: ID, data: CartPatch):
    return response(cart.edit(actor, item_id, data))


@router.delete("/cart/items/{item_id}", status_code=204)
def remove(actor: Actor, item_id: ID):
    cart.remove(actor, item_id)
    return EmptyResponse(status_code=204)
