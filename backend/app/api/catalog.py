from fastapi import APIRouter
from fastapi import Response as EmptyResponse

from ..dependencies import Actor
from ..schemas.catalog import (
    CategoryInput,
    CategoryOut,
    ProductCreate,
    ProductOut,
    ProductPatch,
    StatusInput,
)
from ..schemas.common import Page, Response
from ..services import catalog
from ..value_types import ID, ProductStatus
from .common import Paging, response

router = APIRouter(tags=["FR-02/07 商品分类"])


@router.get("/categories", response_model=Response[list[CategoryOut]])
def categories(actor: Actor):
    return response(catalog.categories(actor))


@router.get("/products", response_model=Response[Page[ProductOut]])
def products(
    actor: Actor,
    paging: Paging,
    keyword: str | None = None,
    category_id: ID | None = None,
    min_price: str | None = None,
    max_price: str | None = None,
):
    return response(
        catalog.products(
            actor,
            keyword=keyword,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            page_number=paging.page,
            page_size=paging.page_size,
        )
    )


@router.get("/products/{product_id}", response_model=Response[ProductOut])
def detail(actor: Actor, product_id: ID):
    return response(catalog.detail(actor, product_id))


@router.get("/admin/categories", response_model=Response[list[CategoryOut]])
def admin_categories(actor: Actor):
    return response(catalog.categories(actor, True))


@router.post("/admin/categories", status_code=201, response_model=Response[CategoryOut])
def category_create(actor: Actor, data: CategoryInput):
    return response(catalog.save_category(actor, data), 201)


@router.patch("/admin/categories/{category_id}", response_model=Response[CategoryOut])
def category_update(actor: Actor, category_id: ID, data: CategoryInput):
    return response(catalog.save_category(actor, data, category_id))


@router.delete("/admin/categories/{category_id}", status_code=204)
def category_delete(actor: Actor, category_id: ID):
    catalog.delete_category(actor, category_id)
    return EmptyResponse(status_code=204)


@router.get("/admin/products", response_model=Response[Page[ProductOut]])
def admin_products(
    actor: Actor,
    paging: Paging,
    keyword: str | None = None,
    category_id: ID | None = None,
    status: ProductStatus | None = None,
):
    return response(
        catalog.products(
            actor,
            True,
            keyword=keyword,
            category_id=category_id,
            status=status,
            page_number=paging.page,
            page_size=paging.page_size,
        )
    )


@router.get("/admin/products/{product_id}", response_model=Response[ProductOut])
def admin_detail(actor: Actor, product_id: ID):
    return response(catalog.detail(actor, product_id, True))


@router.post("/admin/products", status_code=201, response_model=Response[ProductOut])
def product_create(actor: Actor, data: ProductCreate):
    return response(catalog.create_product(actor, data), 201)


@router.patch("/admin/products/{product_id}", response_model=Response[ProductOut])
def product_update(actor: Actor, product_id: ID, data: ProductPatch):
    return response(catalog.edit_product(actor, product_id, data))


@router.put("/admin/products/{product_id}/status", response_model=Response[ProductOut])
def product_status(actor: Actor, product_id: ID, data: StatusInput):
    return response(catalog.edit_product(actor, product_id, data))


@router.delete("/admin/products/{product_id}", status_code=204)
def product_delete(actor: Actor, product_id: ID):
    catalog.delete_product(actor, product_id)
    return EmptyResponse(status_code=204)
