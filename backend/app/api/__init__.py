from fastapi import APIRouter

router = APIRouter()
from . import auth, cart, catalog, inventory, orders, payments, statistics, users

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(catalog.router)
router.include_router(inventory.router)
router.include_router(cart.router)
router.include_router(orders.router)
router.include_router(payments.router)
router.include_router(statistics.router)
