"""Read-only EXPLAIN evidence for contract SQL and actual application pagination."""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", choices=("test", "application"), default="test")
    parser.add_argument("--json", action="store_true", help="Print machine-readable evidence")
    args = parser.parse_args()
    load_dotenv(ROOT / "backend/.env")
    url = os.getenv("TEST_DATABASE_URL" if args.database == "test" else "DATABASE_URL")
    if not url or (args.database == "test" and make_url(url).database != "scu_ecommerce_test"):
        parser.error("Configure the selected database in backend/.env")
    os.environ["DATABASE_URL"] = url
    # Configure the selected database before importing the application's engine.
    from app.database import SessionFactory, engine
    from app.dependencies import Principal
    from app.errors import BusinessError
    from app.queries import sql
    from app.services import catalog, identity, inventory, orders, statistics

    def read_only(dbapi, record, proxy):
        with dbapi.cursor() as cursor:
            cursor.execute("SET SESSION TRANSACTION READ ONLY")

    event.listen(engine, "checkout", read_only)
    try:
        with engine.connect() as connection:
            current = connection.scalar(text("SELECT NOW()"))
            uid = (
                connection.scalar(
                    text(
                        "SELECT user_id FROM orders GROUP BY user_id ORDER BY COUNT(*) DESC LIMIT 1"
                    )
                )
                or 0
            )
            aid = (
                connection.scalar(
                    text("SELECT id FROM users WHERE role='ADMIN' ORDER BY id LIMIT 1")
                )
                or 0
            )
            product = connection.execute(
                text("SELECT id, category_id FROM product ORDER BY id LIMIT 1")
            ).first()
            pid, category_id = product if product else (0, 0)
            readonly = bool(connection.scalar(text("SELECT @@transaction_read_only")))
            if not readonly:
                raise RuntimeError("Read-only transaction configuration was not applied")
            evidence = {
                "database": engine.url.database,
                "mysql_version": connection.scalar(text("SELECT VERSION()")),
                "read_only": readonly,
                "as_of": str(current),
                "row_counts": {
                    name: connection.scalar(text("SELECT COUNT(*) FROM " + name))
                    for name in ("users", "product", "orders", "order_item", "payment", "inventory")
                },
                "queries": [],
            }
        start = current.replace(month=1, day=1, hour=0, minute=0, second=0)
        end = start.replace(year=start.year + 1)
        params = {
            "user_id": uid,
            "status": None,
            "start_at": start,
            "end_at": end,
            "as_of": current,
        }

        def contract(number):
            with SessionFactory() as session:
                session.execute(text(sql(number)), params).all()

        actor, admin = Principal(uid, "USER"), Principal(aid, "ADMIN")
        cases = [(f"Q{number}", lambda number=number: contract(number)) for number in range(1, 5)]
        cases += [
            ("orders_user", lambda: orders.listing(actor)),
            ("orders_admin_pending", lambda: orders.listing(admin, True, status="PENDING")),
            ("products_user", lambda: catalog.products(actor)),
            (
                "products_category_price",
                lambda: catalog.products(
                    actor, category_id=category_id, min_price="1.00", max_price="100.00"
                ),
            ),
            ("products_keyword", lambda: catalog.products(admin, True, keyword="demo")),
            ("inventory_all", lambda: inventory.listing(admin)),
            ("inventory_product", lambda: inventory.listing(admin, product_id=pid)),
            ("users", lambda: identity.users(admin)),
            ("inactive_users", lambda: statistics.inactive(admin, current)),
        ]
        for name, operation in cases:
            statements = []

            def capture(conn, cursor, statement, parameters, context, many):
                if statement.lstrip().upper().startswith(("SELECT", "WITH")):
                    statements.append((statement, parameters))

            event.listen(engine, "before_cursor_execute", capture)
            try:
                operation()
            finally:
                event.remove(engine, "before_cursor_execute", capture)
            plans = []
            with engine.connect() as connection:
                for statement, parameters in statements:
                    rows = connection.exec_driver_sql("EXPLAIN " + statement, parameters).mappings()
                    plans.append(
                        [
                            {
                                key: row[key]
                                for key in (
                                    "select_type",
                                    "table",
                                    "type",
                                    "key",
                                    "rows",
                                    "filtered",
                                    "Extra",
                                )
                            }
                            for row in rows
                        ]
                    )
            evidence["queries"].append(
                {"name": name, "select_count": len(statements), "plans": plans}
            )
        if args.json:
            print(json.dumps(evidence, ensure_ascii=False, indent=2))
        else:
            print(f"MySQL {evidence['mysql_version']} / {evidence['database']} / READ ONLY")
            print(f"as_of={current}; rows are optimizer estimates; no scan-type pass/fail rule")
            print("Table counts: " + json.dumps(evidence["row_counts"]))
            for query in evidence["queries"]:
                print(f"\n{query['name']} ({query['select_count']} SELECT statements)")
                for number, plan in enumerate(query["plans"], 1):
                    for row in plan:
                        print(
                            f"  {number} {row['table'] or '-'}: {row['type'] or '-'} "
                            f"key={row['key'] or '-'} rows={row['rows']} {row['Extra'] or ''}"
                        )
    except (SQLAlchemyError, BusinessError) as exc:
        # DBAPI exceptions may contain SQL parameters and connection credentials.
        raise SystemExit(
            f"Query-plan check failed ({type(exc).__name__}); no data was written."
        ) from None
    finally:
        event.remove(engine, "checkout", read_only)
        engine.dispose()


if __name__ == "__main__":
    main()
