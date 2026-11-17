from sqlalchemy import exists, select, true
from sqlalchemy.exc import IntegrityError

from ..dependencies import require
from ..errors import fail, integrity
from ..models import CartItem, Category, Inventory, OrderItem, Product
from ..queries import page_parts
from ..transactions import constraint_name, read, sqlstate, write
from ..value_types import money
from .common import contains, paged


def category_out(c):
    return {"id": str(c.id), "name": c.name}


def product_out(p, c, inv):
    integrity(inv is not None, "商品缺少库存记录")
    return {
        "id": str(p.id),
        "category_id": str(p.category_id),
        "category_name": c.name,
        "name": p.name,
        "price": p.price,
        "description": p.description,
        "status": p.status,
        "available": inv.available,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


def product_query():
    return (
        select(Product, Category, Inventory)
        .join(Category, Category.id == Product.category_id)
        .outerjoin(Inventory, Inventory.product_id == Product.id)
    )


def get_in_session(s, product_id, admin=True):
    stmt = product_query().where(Product.id == product_id)
    if not admin:
        stmt = stmt.where(Product.status == "ON_SHELF")
    row = s.execute(stmt).first()
    if row is None:
        fail("PRODUCT_NOT_FOUND", 404)
    return product_out(*row)


def browse_permission(actor, admin=False):
    if admin or actor is not None:
        require(actor, "ADMIN" if admin else "USER")


def categories(actor, admin=False):
    browse_permission(actor, admin)
    return read(
        lambda s: [category_out(c) for c in s.scalars(select(Category).order_by(Category.id))]
    )


def products(
    actor,
    admin=False,
    keyword=None,
    category_id=None,
    status=None,
    min_price=None,
    max_price=None,
    page_number=1,
    page_size=20,
):
    browse_permission(actor, admin)
    lower = money(min_price, "PRICE_RANGE_INVALID", True) if min_price is not None else None
    upper = money(max_price, "PRICE_RANGE_INVALID", True) if max_price is not None else None
    if lower is not None and upper is not None and lower > upper:
        fail("PRICE_RANGE_INVALID", 422)

    def query(s):
        stmt = select(Product.id)
        if not admin:
            stmt = stmt.where(Product.status == "ON_SHELF")
        elif status:
            stmt = stmt.where(Product.status == status)
        if keyword:
            stmt = stmt.where(contains(Product.name, keyword))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if lower is not None:
            stmt = stmt.where(Product.price >= lower)
        if upper is not None:
            stmt = stmt.where(Product.price <= upper)
        page_rows, totals = page_parts(stmt, page_number, page_size)
        rows = s.execute(
            select(totals.c.total, Product, Category, Inventory)
            .select_from(totals.outerjoin(page_rows, true()))
            .outerjoin(Product, Product.id == page_rows.c.id)
            .outerjoin(Category, Category.id == Product.category_id)
            .outerjoin(Inventory, Inventory.product_id == Product.id)
            .order_by(Product.id)
        ).all()
        items = [product_out(p, c, inv) for _, p, c, inv in rows if p is not None]
        return paged(items, rows[0][0], page_number, page_size)

    return read(query)


def detail(actor, product_id, admin=False):
    browse_permission(actor, admin)
    return read(lambda s: get_in_session(s, product_id, admin))


def save_category(actor, data, category_id=None):
    require(actor, "ADMIN")

    def change(s):
        c = s.get(Category, category_id, with_for_update=True) if category_id else Category()
        if c is None:
            fail("CATEGORY_NOT_FOUND", 404)
        c.name = data.name
        s.add(c)
        s.flush()
        return category_out(c)

    try:
        return write(change)
    except IntegrityError as exc:
        if sqlstate(exc) == "23505" and constraint_name(exc) == "uk_category_name":
            fail("CATEGORY_NAME_EXISTS", 409)
        raise


def delete_category(actor, category_id):
    require(actor, "ADMIN")

    def change(s):
        c = s.get(Category, category_id, with_for_update=True)
        if c is None:
            fail("CATEGORY_NOT_FOUND", 404)
        if s.scalar(select(exists().where(Product.category_id == category_id))):
            fail("CATEGORY_IN_USE")
        s.delete(c)
        s.flush()

    try:
        write(change)
    except IntegrityError as exc:
        if sqlstate(exc) == "23503":
            fail("CATEGORY_IN_USE")
        raise


def create_in_session(s, data):
    if not s.get(Category, data.category_id):
        fail("CATEGORY_NOT_FOUND", 404)
    p = Product(**data.model_dump())
    s.add(p)
    s.flush()
    s.add(Inventory(product_id=p.id, available=0, version=0))
    s.flush()
    return get_in_session(s, p.id)


def create_product(actor, data):
    require(actor, "ADMIN")
    try:
        return write(lambda s: create_in_session(s, data))
    except IntegrityError as exc:
        if sqlstate(exc) == "23503" and constraint_name(exc) == "fk_product_category":
            fail("CATEGORY_NOT_FOUND", 404)
        raise


def edit_product(actor, product_id, data):
    require(actor, "ADMIN")

    def change(s):
        p = s.get(Product, product_id, with_for_update=True)
        if not p:
            fail("PRODUCT_NOT_FOUND", 404)
        integrity(
            s.scalar(select(Inventory).where(Inventory.product_id == product_id).with_for_update())
            is not None
        )
        if "category_id" in data.model_fields_set and not s.get(Category, data.category_id):
            fail("CATEGORY_NOT_FOUND", 404)
        for key in data.model_fields_set:
            setattr(p, key, getattr(data, key))
        s.flush()
        s.refresh(p)
        return get_in_session(s, p.id)

    try:
        return write(change)
    except IntegrityError as exc:
        if sqlstate(exc) == "23503" and constraint_name(exc) == "fk_product_category":
            fail("CATEGORY_NOT_FOUND", 404)
        raise


def delete_product(actor, product_id):
    require(actor, "ADMIN")

    def change(s):
        p = s.get(Product, product_id, with_for_update=True)
        if p is None:
            fail("PRODUCT_NOT_FOUND", 404)
        inv = s.scalar(
            select(Inventory).where(Inventory.product_id == product_id).with_for_update()
        )
        integrity(inv is not None)
        if s.scalar(select(exists().where(CartItem.product_id == product_id))) or s.scalar(
            select(exists().where(OrderItem.product_id == product_id))
        ):
            fail("PRODUCT_IN_USE")
        if inv.available:
            fail("INVENTORY_NOT_ZERO")
        s.delete(inv)
        s.flush()
        s.delete(p)
        s.flush()

    try:
        write(change)
    except IntegrityError as exc:
        if sqlstate(exc) == "23503":
            fail("PRODUCT_IN_USE")
        raise
