import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from db.bootstrap import initialize

load_dotenv(Path(__file__).resolve().parents[1] / "backend/.env")
test_url = os.getenv("TEST_DATABASE_URL")
if (
    not test_url
    or make_url(test_url).drivername != "postgresql+psycopg"
    or make_url(test_url).database != "scu_ecommerce_test"
    or test_url == os.getenv("DATABASE_URL")
):
    raise RuntimeError("Configure a separate TEST_DATABASE_URL ending in scu_ecommerce_test")
os.environ["DATABASE_URL"] = test_url

from app.database import engine

from tests.fixtures import accounts as accounts
from tests.fixtures import goods as goods
from tests.fixtures import placed as placed


@pytest.fixture(scope="session", autouse=True)
def database():
    admin = create_engine(make_url(test_url).set(database="postgres"))
    with admin.connect() as c:
        count = c.scalar(
            text("SELECT COUNT(*) FROM pg_database WHERE datname='scu_ecommerce_test'")
        )
    admin.dispose()
    if count:
        with engine.connect() as c:
            count = c.scalar(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
            )
    if not count:
        initialize(test_url)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean(database):
    with engine.begin() as c:
        for table in (
            "payment",
            "order_item",
            "orders",
            "cart_item",
            "cart",
            "inventory",
            "product",
            "category",
            "users",
        ):
            c.execute(text(f"DELETE FROM {table}"))


@pytest.fixture
def client():
    from app.main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
