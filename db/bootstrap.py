"""Execute the frozen schema into an empty, explicitly selected database."""

import argparse
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def initialize(url_string):
    url = make_url(url_string)
    name = url.database
    if name not in ("scu_ecommerce", "scu_ecommerce_test"):
        raise ValueError("Only scu_ecommerce or scu_ecommerce_test may be initialized")
    engine = create_engine(url.set(database=""), isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            version = conn.scalar(text("SELECT VERSION()"))
            if tuple(map(int, version.split("-")[0].split(".")[:3])) < (8, 0, 16):
                raise ValueError("MySQL 8.0.16+ required")
            existing = conn.scalar(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=:name"),
                {"name": name},
            )
            if existing:
                raise ValueError("Target database is not empty; schema was not changed")
            ddl = (ROOT / "db/schema.sql").read_text(encoding="utf-8")
            ddl = re.sub(r"\bscu_ecommerce\b", name, ddl)
            for statement in ddl.split(";"):
                if statement.strip():
                    conn.exec_driver_sql(statement.strip())
    finally:
        engine.dispose()


if __name__ == "__main__":
    load_dotenv(ROOT / "backend/.env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    key = "TEST_DATABASE_URL" if args.test else "DATABASE_URL"
    if not os.getenv(key):
        raise SystemExit(f"Configure {key} first")
    initialize(os.environ[key])
    print("Empty database initialized from the frozen DDL")
