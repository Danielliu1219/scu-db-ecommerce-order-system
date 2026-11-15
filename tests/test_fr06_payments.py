import pytest
from app.database import SessionFactory
from app.models import Order, Payment
from app.schemas.payments import Simulate
from app.services import payments
from sqlalchemy import event, func, select

from tests.fixtures import auth


def test_failure_success_and_repeated_failure_returns_success(client, accounts, placed):
    order, _ = placed
    oid = order["order_id"]
    h = auth(accounts["alice"])
    path = f"/api/v1/orders/{oid}/payments/simulate"
    assert (
        client.post(path, headers=h, json={"simulate_result": "FAILURE"}).json()["data"]["payment"]
        is None
    )
    assert client.post(path, headers=h, json={"simulate_result": "FAILURE"}).status_code == 200
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Payment)) == 0
        assert s.get(Order, int(oid)).status == "PENDING"
    first = client.post(path, headers=h, json={"simulate_result": "SUCCESS"})
    assert first.status_code == 201 and first.json()["data"]["amount"] == "80.00"
    repeated = client.post(path, headers=h, json={"simulate_result": "FAILURE"})
    assert repeated.status_code == 200 and repeated.json()["data"]["result"] == "SUCCESS"
    assert repeated.json()["data"]["payment_id"] == first.json()["data"]["payment_id"]
    assert (
        client.get(f"/api/v1/orders/{oid}/payment", headers=auth(accounts["bob"])).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/admin/payments?order_id={oid}", headers=auth(accounts["admin"])
        ).json()["data"]["payment"]["amount"]
        == "80.00"
    )
    assert (
        client.post(
            path, headers=h, json={"simulate_result": "SUCCESS", "amount": "0.01"}
        ).status_code
        == 422
    )
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Payment)) == 1


def test_payment_failure_rolls_back_order_and_record(monkeypatch, accounts, placed):
    order, _ = placed
    oid = int(order["order_id"])

    def reject(conn, cursor, statement, parameters, context, many):
        if statement.startswith("UPDATE orders") and "paid_at" in statement:
            raise RuntimeError("injected order state failure")

    from app.database import engine

    event.listen(engine, "before_cursor_execute", reject)
    try:
        with pytest.raises(RuntimeError):
            payments.simulate(accounts["alice"], oid, Simulate(simulate_result="SUCCESS"))
    finally:
        event.remove(engine, "before_cursor_execute", reject)
    with SessionFactory() as s:
        assert s.get(Order, oid).status == "PENDING"
        assert s.scalar(select(func.count()).select_from(Payment)) == 0
