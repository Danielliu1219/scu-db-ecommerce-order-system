import re
from pathlib import Path

from app.database import engine
from app.models import Base
from sqlalchemy import inspect, text

ROOT = Path(__file__).resolve().parents[1]


def test_schema_is_frozen_ddl():
    doc = (ROOT / "docs/03-database-design.md").read_text(encoding="utf-8")
    ddl = re.search(r"## 4 PostgreSQL.*?```sql\n(.*?)```", doc, re.S).group(1)
    assert (ROOT / "db/schema.sql").read_text(encoding="utf-8") == ddl


def test_nine_mappings_match_live_database():
    db = inspect(engine)
    assert set(db.get_table_names()) == set(Base.metadata.tables)
    for name, table in Base.metadata.tables.items():
        columns = db.get_columns(name)
        assert [c["name"] for c in columns] == list(table.columns.keys())
        for column in columns:
            mapped = table.c[column["name"]]
            assert (
                str(column["type"].compile(dialect=engine.dialect))
                == str(mapped.type.compile(dialect=engine.dialect))
            )
            assert column["nullable"] == mapped.nullable
        assert {c["name"] for c in db.get_check_constraints(name)} == {
            c.name for c in table.constraints if c.__class__.__name__ == "CheckConstraint"
        }
        assert {f["name"] for f in db.get_foreign_keys(name)} == {
            c.name for c in table.foreign_key_constraints
        }
        live_indexes = {i["name"]: tuple(i["column_names"]) for i in db.get_indexes(name)}
        expected = {i.name: tuple(c.name for c in i.columns) for i in table.indexes}
        expected.update(
            {
                c.name: tuple(c.columns.keys())
                for c in table.constraints
                if c.__class__.__name__ == "UniqueConstraint"
            }
        )
        assert live_indexes == expected


def test_connection_settings():
    with engine.connect() as c:
        row = c.execute(
            text(
                "SELECT current_setting('transaction_isolation'), current_setting('TimeZone'), current_setting('client_encoding')"
            )
        ).one()
        assert tuple(row) == ("read committed", "Asia/Shanghai", "UTF8")


def test_live_checks_and_foreign_keys_reject_invalid_writes(accounts, goods, placed):
    import pytest
    from app.database import SessionFactory
    from sqlalchemy.exc import DBAPIError

    with SessionFactory.begin() as s:
        for statement, params in [
            (
                "UPDATE inventory SET available=-1 WHERE product_id=:id",
                {"id": int(goods[0]["id"])},
            ),
            ("UPDATE product SET price=0 WHERE id=:id", {"id": int(goods[0]["id"])}),
            (
                "UPDATE orders SET status='PAID' WHERE id=:id",
                {"id": int(placed[0]["order_id"])},
            ),
            (
                "UPDATE product SET category_id=18446744073709551615 WHERE id=:id",
                {"id": int(goods[0]["id"])},
            ),
        ]:
            with pytest.raises(DBAPIError) as failure:
                with s.begin_nested():
                    s.execute(text(statement), params)
            assert failure.value.orig.sqlstate in ("23514", "23503")
