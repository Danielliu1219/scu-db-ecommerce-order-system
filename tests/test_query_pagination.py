from datetime import timedelta

import pytest
from app.database import SessionFactory, engine
from app.models import Order, User
from app.schemas.catalog import ProductCreate, StatusInput
from app.schemas.identity import Register
from app.services import catalog, identity, inventory, orders, statistics
from app.services.common import now
from sqlalchemy import event, update

from tests.fixtures import PASSWORD, checkout_data


@pytest.mark.parametrize("kind", ["orders", "products", "inventory", "users", "inactive"])
def test_pages_keep_total_on_empty_page_and_use_one_data_statement(accounts, goods, placed, kind):
    actor, admin = accounts["alice"], accounts["admin"]
    for _ in range(2):
        orders.checkout(actor, checkout_data(actor, goods))
    with SessionFactory.begin() as s:
        cutoff = now(s)
        s.execute(update(User).values(created_at=cutoff - timedelta(days=40)))
        s.execute(update(Order).values(created_at=cutoff - timedelta(days=31)))
    operations = {
        "orders": (lambda **kw: orders.listing(actor, **kw), 3, "order_id", {"status": "PAID"}),
        "products": (lambda **kw: catalog.products(actor, **kw), 2, "id", {"keyword": "missing"}),
        "inventory": (lambda **kw: inventory.listing(admin, **kw), 2, "id", {"keyword": "missing"}),
        "users": (lambda **kw: identity.users(admin, **kw), 2, "id", {"username": "missing"}),
        "inactive": (
            lambda **kw: statistics.inactive(admin, **kw),
            2,
            "user_id",
            {"as_of": cutoff - timedelta(days=50)},
        ),
    }
    operation, expected, id_key, empty_filter = operations[kind]
    reads = []

    def record(conn, cursor, statement, parameters, context, many):
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            # Acquiring the fixed cutoff is separate from the single count+page query.
            if " FROM " in " ".join(statement.upper().split()):
                reads.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        first = operation(page_number=1, page_size=1)
        second = operation(page_number=2, page_size=1)
        beyond = operation(page_number=99, page_size=1)
        empty = operation(**empty_filter)
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert len(reads) == 4
    assert first["total"] == second["total"] == beyond["total"] == expected
    assert len(first["items"]) == len(second["items"]) == 1
    assert first["items"][0][id_key] != second["items"][0][id_key]
    assert beyond["items"] == [] and empty["items"] == [] and empty["total"] == 0
    if kind == "orders":
        whole = operation(page_size=2)
        assert len(whole["items"]) == 2
        assert [len(o["items"]) for o in whole["items"]] == [2, 2]


@pytest.mark.parametrize("kind", ["products", "inventory", "users"])
def test_total_and_rows_do_not_mix_concurrent_commits(accounts, goods, kind):
    admin, actor = accounts["admin"], accounts["alice"]
    reads, changing = [], False

    def change_after_read(conn, cursor, statement, parameters, context, many):
        nonlocal changing
        if changing or not statement.lstrip().upper().startswith(("SELECT", "WITH")):
            return
        reads.append(statement)
        if len(reads) != 1:
            return
        changing = True
        try:
            if kind == "products":
                catalog.edit_product(admin, int(goods[0]["id"]), StatusInput(status="OFF_SHELF"))
            elif kind == "inventory":
                catalog.create_product(
                    admin,
                    ProductCreate(
                        category_id=goods[0]["category_id"],
                        name="New stock",
                        price="1.00",
                        description="",
                    ),
                )
            else:
                identity.register(
                    Register(username="new_user", password=PASSWORD, nickname="new", phone="test")
                )
        finally:
            changing = False

    operation = {
        "products": lambda: catalog.products(actor),
        "inventory": lambda: inventory.listing(admin),
        "users": lambda: identity.users(admin),
    }[kind]
    event.listen(engine, "after_cursor_execute", change_after_read)
    try:
        result = operation()
    finally:
        event.remove(engine, "after_cursor_execute", change_after_read)
    assert len(reads) == 1
    assert result["total"] == len(result["items"]) == 2
    assert operation()["total"] == (1 if kind == "products" else 3)
