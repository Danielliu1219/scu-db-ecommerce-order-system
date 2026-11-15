import json
import subprocess
import sys
from pathlib import Path

from app.database import SessionFactory
from sqlalchemy import text


def test_plan_cli_is_read_only_and_covers_contract_and_pagination(accounts, goods, placed):
    tables = (
        "users",
        "product",
        "inventory",
        "orders",
        "order_item",
        "payment",
        "cart",
        "cart_item",
    )

    def snapshot():
        with SessionFactory() as session:
            return {
                name: session.execute(text("SELECT * FROM " + name + " ORDER BY id")).all()
                for name in tables
            }

    before = snapshot()
    result = subprocess.run(
        [sys.executable, "-m", "db.query_plan", "--json"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    evidence = json.loads(result.stdout)
    assert evidence["database"] == "scu_ecommerce_test" and evidence["read_only"] is True
    queries = {query["name"]: query for query in evidence["queries"]}
    assert set(queries) == {
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "orders_user",
        "orders_admin_pending",
        "products_user",
        "products_category_price",
        "products_keyword",
        "inventory_all",
        "inventory_product",
        "users",
        "inactive_users",
    }
    for name, query in queries.items():
        assert query["select_count"] == (2 if name == "inactive_users" else 1)
        assert query["plans"]
    assert snapshot() == before
