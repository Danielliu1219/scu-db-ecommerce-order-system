import pymysql
import pytest
from app import transactions
from app.database import SessionFactory
from app.errors import BusinessError
from app.models import Inventory
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


@pytest.mark.parametrize("code", [1205, 1213])
def test_retry_rolls_back_whole_attempt_and_uses_fresh_session(monkeypatch, accounts, goods, code):
    sessions = []
    waits = []
    monkeypatch.setattr(transactions.time, "sleep", lambda seconds: waits.append(seconds))

    def operation(s):
        sessions.append(s)
        s.execute(
            update(Inventory)
            .where(Inventory.product_id == int(goods[0]["id"]))
            .values(available=Inventory.available - 1, version=Inventory.version + 1)
        )
        if len(sessions) < 3:
            raise OperationalError("injected", {}, pymysql.err.OperationalError(code, "injected"))
        return "committed"

    assert transactions.write(operation) == "committed"
    assert len({id(s) for s in sessions}) == 3 and len(waits) == 2
    with SessionFactory() as s:
        inv = s.scalar(select(Inventory).where(Inventory.product_id == int(goods[0]["id"])))
        assert (inv.available, inv.version) == (19, 2)


def test_retry_exhausted_has_no_partial_write(monkeypatch, accounts, goods):
    monkeypatch.setattr(transactions.time, "sleep", lambda _: None)

    def operation(s):
        s.execute(update(Inventory).values(available=0))
        raise OperationalError("injected", {}, pymysql.err.OperationalError(1213, "injected"))

    with pytest.raises(BusinessError) as error:
        transactions.write(operation)
    assert error.value.code == "TRANSACTION_RETRY_EXHAUSTED"
    with SessionFactory() as s:
        assert all(i.available == 20 for i in s.scalars(select(Inventory)))


def test_commit_response_lost_is_resolved_without_repeat(monkeypatch, accounts, goods):
    original = Session.commit
    calls = []

    def lost(self):
        original(self)
        raise OperationalError(
            "COMMIT",
            {},
            pymysql.err.OperationalError(2013, "lost response"),
            connection_invalidated=True,
        )

    monkeypatch.setattr(Session, "commit", lost)
    pid = int(goods[0]["id"])

    def operation(s):
        calls.append(1)
        s.execute(
            update(Inventory)
            .where(Inventory.product_id == pid)
            .values(available=Inventory.available + 1)
        )
        return 21

    def resolve(s):
        return s.scalar(select(Inventory.available).where(Inventory.product_id == pid))

    assert transactions.write(operation, resolve) == 21 and len(calls) == 1


def test_unknown_nonidempotent_operation_is_not_replayed(monkeypatch, accounts, goods):
    original = Session.commit
    calls = []

    def lost(self):
        original(self)
        raise OperationalError(
            "COMMIT",
            {},
            pymysql.err.OperationalError(2013, "lost response"),
            connection_invalidated=True,
        )

    monkeypatch.setattr(Session, "commit", lost)

    def operation(s):
        calls.append(1)
        s.execute(update(Inventory).values(available=Inventory.available + 1))

    with pytest.raises(BusinessError) as error:
        transactions.write(operation)
    assert error.value.details == {"outcome": "UNKNOWN"} and len(calls) == 1
