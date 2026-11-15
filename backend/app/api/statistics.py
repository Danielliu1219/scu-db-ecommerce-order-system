from fastapi import APIRouter

from ..dependencies import Actor
from ..schemas.common import Response
from ..schemas.statistics import InactivePage, MonthlySales, TopProduct
from ..services import statistics
from .common import Paging, response

router = APIRouter(tags=["FR-09 统计"])


@router.get("/admin/statistics/monthly-sales", response_model=Response[list[MonthlySales]])
def monthly(actor: Actor, paid_start: str | None = None, paid_end: str | None = None):
    return response(statistics.sales(actor, paid_start, paid_end))


@router.get("/admin/statistics/top-products", response_model=Response[list[TopProduct]])
def top(actor: Actor, paid_start: str | None = None, paid_end: str | None = None):
    return response(statistics.sales(actor, paid_start, paid_end, True))


@router.get("/admin/statistics/inactive-users", response_model=Response[InactivePage])
def inactive(actor: Actor, paging: Paging, as_of: str | None = None):
    return response(statistics.inactive(actor, as_of, paging.page, paging.page_size))
