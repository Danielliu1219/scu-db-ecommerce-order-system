import pytest
from app.database import SessionFactory, engine
from app.models import Inventory
from app.schemas.payments import Simulate
from app.services import orders, payments
from sqlalchemy import event, select

from tests.fixtures import auth, checkout_data


def test_filtered_page_is_one_statement_snapshot(accounts, placed):
    actor = accounts["alice"]
    oid = int(placed[0]["order_id"])
    reads = []
    changing = False

    def cancel_after_read(conn, cursor, statement, parameters, context, many):
        nonlocal changing
        if changing or "orders" not in statement.lower():
            return
        if not statement.lstrip().upper().startswith(("SELECT", "WITH")):
            return
        reads.append(statement)
        if len(reads) == 1:
            # Another connection commits after this statement's snapshot was read.
            changing = True
            try:
                orders.cancel(actor, oid)
            finally:
                changing = False

    event.listen(engine, "after_cursor_execute", cancel_after_read)
    try:
        result = orders.listing(actor, status="PENDING")
    finally:
        event.remove(engine, "after_cursor_execute", cancel_after_read)
    assert result["total"] == 1 and len(result["items"]) == 1
    assert result["items"][0]["status"] == "PENDING"
    assert len(result["items"][0]["items"]) == 2
    assert len(reads) == 1
    assert orders.detail(actor, oid)["status"] == "CANCELLED"


@pytest.mark.parametrize(
    "start,end",
    [
        ("0001-01-01T00:00:00+14:00", "2026-12-01"),
        ("2026-01-01", "9999-12-31T23:59:59-14:00"),
    ],
)
def test_time_conversion_overflow_returns_contract_error(client, accounts, start, end):
    response = client.get(
        "/api/v1/orders",
        headers=auth(accounts["alice"]),
        params={"created_start": start, "created_end": end},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TIME_RANGE_INVALID"


@pytest.mark.parametrize(
    "params",
    [
        {"created_start": "2026-11-01"},
        {"created_end": "2026-12-01"},
        {"created_start": "2026-12-01", "created_end": "2026-11-01"},
        {"created_start": "2026-11-01", "created_end": "2026-11-01"},
    ],
)
def test_order_time_range_rejects_partial_or_reversed(client, accounts, params):
    for path, actor in [("/orders", accounts["alice"]), ("/admin/orders", accounts["admin"])]:
        r = client.get("/api/v1" + path, headers=auth(actor), params=params)
        assert r.status_code == 422 and r.json()["error"]["code"] == "TIME_RANGE_INVALID"


def test_order_role_and_ownership_rejections_leave_state_intact(client, accounts, placed):
    oid = placed[0]["order_id"]
    for who, method, path, body, status in [
        ("bob", "get", f"/orders/{oid}", None, 404),
        ("bob", "post", f"/orders/{oid}/cancel", None, 404),
        ("bob", "post", f"/orders/{oid}/payments/simulate", {"simulate_result": "SUCCESS"}, 404),
        ("admin", "post", f"/orders/{oid}/cancel", None, 403),
        ("admin", "post", f"/orders/{oid}/payments/simulate", {"simulate_result": "SUCCESS"}, 403),
        ("alice", "post", f"/admin/orders/{oid}/ship", None, 403),
    ]:
        r = client.request(method, "/api/v1" + path, headers=auth(accounts[who]), json=body)
        assert r.status_code == status
        assert r.json()["error"]["code"] == (
            "ORDER_NOT_FOUND" if status == 404 else "ROLE_FORBIDDEN"
        )
    result = orders.detail(accounts["alice"], int(oid))
    assert result["status"] == "PENDING" and result["payment"] is None


def test_order_time_window_is_half_open_and_accepts_equivalent_offsets(
    client, accounts, goods, placed
):
    from datetime import datetime

    from app.models import Order
    from sqlalchemy import update

    actor = accounts["alice"]
    second, _ = orders.checkout(actor, checkout_data(actor, goods))
    with SessionFactory.begin() as s:
        s.execute(
            update(Order)
            .where(Order.id == int(placed[0]["order_id"]))
            .values(created_at=datetime(2026, 11, 1))
        )
        s.execute(
            update(Order)
            .where(Order.id == int(second["order_id"]))
            .values(created_at=datetime(2026, 12, 1))
        )
    for start, end in [
        ("2026-11-01T00:00:00+08:00", "2026-12-01T00:00:00+08:00"),
        ("2026-10-31T16:00:00+00:00", "2026-11-30T16:00:00+00:00"),
    ]:
        r = client.get(
            "/api/v1/orders",
            headers=auth(actor),
            params={"created_start": start, "created_end": end},
        )
        assert r.status_code == 200
        assert r.json()["data"]["total"] == 1
        assert r.json()["data"]["items"][0]["order_id"] == placed[0]["order_id"]
    assert client.get("/api/v1/orders", headers=auth(actor)).json()["data"]["total"] == 2


def test_cancel_is_once_and_permissions(client, accounts, goods, placed):
    order, _ = placed
    oid = order["order_id"]
    h = auth(accounts["alice"])
    assert client.get("/api/v1/orders/" + oid, headers=auth(accounts["bob"])).status_code == 404
    assert (
        client.post(
            "/api/v1/orders/" + oid + "/cancel", headers=auth(accounts["admin"])
        ).status_code
        == 403
    )
    first = client.post("/api/v1/orders/" + oid + "/cancel", headers=h)
    assert first.status_code == 200 and first.json()["data"]["status"] == "CANCELLED"
    assert (
        client.post("/api/v1/orders/" + oid + "/cancel", headers=h).json()["data"]["cancelled_at"]
        == first.json()["data"]["cancelled_at"]
    )
    with SessionFactory() as s:
        assert [i.available for i in s.scalars(select(Inventory).order_by(Inventory.id))] == [
            20,
            20,
        ]


def test_state_machine_and_order_pagination(client, accounts, goods, placed):
    order, _ = placed
    oid = int(order["order_id"])
    actor = accounts["alice"]
    admin = accounts["admin"]
    assert client.post(f"/api/v1/admin/orders/{oid}/ship", headers=auth(admin)).status_code == 409
    payments.simulate(actor, oid, Simulate(simulate_result="SUCCESS"))
    shipped = orders.advance(admin, oid, True)
    complete = orders.advance(actor, oid)
    assert (
        complete["created_at"]
        <= complete["paid_at"]
        <= complete["shipped_at"]
        <= complete["completed_at"]
    )
    assert orders.advance(admin, oid, True)["shipped_at"] == shipped["shipped_at"]
    assert orders.advance(actor, oid)["completed_at"] == complete["completed_at"]
    assert client.post(f"/api/v1/orders/{oid}/cancel", headers=auth(actor)).status_code == 409
    orders.checkout(actor, checkout_data(actor, goods))
    listing = client.get("/api/v1/orders?page_size=1", headers=auth(actor)).json()["data"]
    assert (
        listing["total"] == 2
        and len(listing["items"]) == 1
        and len(listing["items"][0]["items"]) == 2
    )


def test_cancel_second_item_overflow_rolls_back_first(accounts, goods, placed):
    import pytest
    from app.errors import BusinessError
    from app.schemas.inventory import Count
    from app.services import inventory
    from app.value_types import INT_MAX

    oid = int(placed[0]["order_id"])
    inventory.maintain(
        accounts["admin"],
        int(goods[1]["id"]),
        Count(counted_available=INT_MAX, expected_version="2"),
        True,
    )
    with pytest.raises(BusinessError) as error:
        orders.cancel(accounts["alice"], oid)
    assert error.value.code == "QUANTITY_OVERFLOW"
    with SessionFactory() as s:
        assert [
            (i.available, i.version) for i in s.scalars(select(Inventory).order_by(Inventory.id))
        ] == [
            (18, 2),
            (INT_MAX, 3),
        ]
    assert orders.detail(accounts["alice"], oid)["status"] == "PENDING"
