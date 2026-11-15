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


def test_real_mysql_lock_timeout_rolls_back_before_retry(monkeypatch, accounts, goods):
    from sqlalchemy import text

    blocked, other = [int(p["id"]) for p in goods]
    sessions, codes = [], []
    original_code = transactions.mysql_code

    def capture_code(exc):
        code = original_code(exc)
        codes.append(code)
        return code

    monkeypatch.setattr(transactions, "mysql_code", capture_code)
    with SessionFactory() as blocker:
        blocker.scalar(select(Inventory).where(Inventory.product_id == blocked).with_for_update())

        def released_before_wait(_):
            assert sessions[0].get_transaction() is None
            with SessionFactory() as check:
                assert (
                    check.scalar(select(Inventory.available).where(Inventory.product_id == other))
                    == 20
                )
            blocker.rollback()

        monkeypatch.setattr(transactions.time, "sleep", released_before_wait)

        def operation(s):
            sessions.append(s)
            original_timeout = s.scalar(text("SELECT @@innodb_lock_wait_timeout"))
            s.execute(text("SET SESSION innodb_lock_wait_timeout=1"))
            try:
                for pid in (other, blocked):
                    s.execute(
                        update(Inventory)
                        .where(Inventory.product_id == pid)
                        .values(available=Inventory.available - 1, version=Inventory.version + 1)
                    )
            finally:
                s.execute(
                    text("SET SESSION innodb_lock_wait_timeout=:timeout"),
                    {"timeout": original_timeout},
                )

        transactions.write(operation)
    assert codes == [1205] and len({id(s) for s in sessions}) == 2
    with SessionFactory() as s:
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (19, 2),
            (19, 2),
        ]


def test_real_mysql_deadlock_retries_whole_transaction(monkeypatch, accounts, goods):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    barrier = Barrier(2)
    codes, attempts = [], [[], []]
    original_code = transactions.mysql_code

    def capture_code(exc):
        code = original_code(exc)
        codes.append(code)
        return code

    monkeypatch.setattr(transactions, "mysql_code", capture_code)
    monkeypatch.setattr(transactions.time, "sleep", lambda _: None)
    ids = [int(p["id"]) for p in goods]

    def participant(index):
        def operation(s):
            attempts[index].append(s)
            # Deliberately reverse locks only in this test to exercise native 1213.
            for position, pid in enumerate(ids if index == 0 else ids[::-1]):
                s.execute(
                    update(Inventory)
                    .where(Inventory.product_id == pid)
                    .values(available=Inventory.available - 1, version=Inventory.version + 1)
                )
                if position == 0 and len(attempts[index]) == 1:
                    barrier.wait(timeout=5)

        transactions.write(operation)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(participant, index) for index in range(2)]
        for future in futures:
            future.result(timeout=20)
    assert codes == [1213]
    assert sorted(len(attempt) for attempt in attempts) == [1, 2]
    assert all(len({id(s) for s in attempt}) == len(attempt) for attempt in attempts)
    with SessionFactory() as s:
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (18, 3),
            (18, 3),
        ]


@pytest.mark.parametrize("operation_name", ["checkout", "cancel", "payment"])
def test_business_commit_response_loss_returns_original_fact(
    monkeypatch, accounts, goods, placed, operation_name
):
    from app.models import Order, Payment
    from app.schemas.payments import Simulate
    from app.services import orders, payments
    from sqlalchemy import func

    from tests.fixtures import checkout_data

    actor, oid = accounts["alice"], int(placed[0]["order_id"])
    if operation_name == "checkout":
        data = checkout_data(actor, goods)

        def operation():
            return orders.checkout(actor, data)

        expected_stock, expected_orders, expected_payments = [(16, 3), (18, 3)], 2, 0
    elif operation_name == "cancel":

        def operation():
            return orders.cancel(actor, oid)

        expected_stock, expected_orders, expected_payments = [(20, 3), (20, 3)], 1, 0
    else:

        def operation():
            return payments.simulate(actor, oid, Simulate(simulate_result="SUCCESS"))

        expected_stock, expected_orders, expected_payments = [(18, 2), (19, 2)], 1, 1
    original, commits = Session.commit, []

    def lose_once(self):
        original(self)
        commits.append(1)
        if len(commits) == 1:
            raise OperationalError(
                "COMMIT",
                {},
                pymysql.err.OperationalError(2013, "lost"),
                connection_invalidated=True,
            )

    monkeypatch.setattr(Session, "commit", lose_once)
    first = operation()
    assert len(commits) == 1  # Resolution is read-only, with no write replay.
    assert operation() == first
    with SessionFactory() as s:
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == expected_stock
        assert s.scalar(select(func.count()).select_from(Order)) == expected_orders
        assert s.scalar(select(func.count()).select_from(Payment)) == expected_payments


def test_checkout_unknown_without_committed_fact_does_not_retry(monkeypatch, accounts, goods):
    from app.models import CartItem, Order
    from app.services import orders
    from sqlalchemy import func

    from tests.fixtures import checkout_data

    data = checkout_data(accounts["alice"], goods)
    original, attempts = Session.commit, []

    def no_commit(self):
        attempts.append(1)
        raise OperationalError(
            "COMMIT", {}, pymysql.err.OperationalError(2013, "lost"), connection_invalidated=True
        )

    monkeypatch.setattr(Session, "commit", no_commit)
    with pytest.raises(BusinessError) as error:
        orders.checkout(accounts["alice"], data)
    assert error.value.status == 503 and error.value.details == {"outcome": "UNKNOWN"}
    assert len(attempts) == 1
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Order)) == 0
        assert s.scalar(select(func.count()).select_from(CartItem)) == 2
        assert [(i.available, i.version) for i in s.scalars(select(Inventory))] == [
            (20, 1),
            (20, 1),
        ]
    monkeypatch.setattr(Session, "commit", original)
    assert orders.checkout(accounts["alice"], data)[1] == 201


def test_stock_commit_response_loss_is_503_and_old_version_cannot_restock_twice(
    monkeypatch, accounts, goods
):
    from app.schemas.inventory import Restock
    from app.services import inventory

    original = Session.commit
    pid = int(goods[0]["id"])
    data = Restock(quantity=3, expected_version="1")

    def lost(self):
        original(self)
        raise OperationalError(
            "COMMIT", {}, pymysql.err.OperationalError(2013, "lost"), connection_invalidated=True
        )

    monkeypatch.setattr(Session, "commit", lost)
    with pytest.raises(BusinessError) as error:
        inventory.maintain(accounts["admin"], pid, data)
    assert error.value.status == 503 and error.value.details == {"outcome": "UNKNOWN"}
    monkeypatch.setattr(Session, "commit", original)
    with pytest.raises(BusinessError) as conflict:
        inventory.maintain(accounts["admin"], pid, data)
    assert conflict.value.code == "INVENTORY_VERSION_CONFLICT"
    with SessionFactory() as s:
        inv = s.scalar(select(Inventory).where(Inventory.product_id == pid))
        assert (inv.available, inv.version) == (23, 2)
