import re
from pathlib import Path

from app.main import app


def test_all_frozen_routes_exist_exactly():
    doc = (Path(__file__).resolve().parents[1] / "docs/03-database-design.md").read_text(
        encoding="utf-8"
    )
    expected = {
        (method, "/api/v1" + path)
        for method, path in re.findall(r"^\| (GET|POST|PUT|PATCH|DELETE) (/[^ |]+)", doc, re.M)
    }
    actual = {
        (method, path)
        for path, entry in app.openapi()["paths"].items()
        for method in [m.upper() for m in entry]
        if path.startswith("/api/v1")
    }
    assert expected == actual


def test_identifier_openapi_is_string_and_auth_errors_do_not_echo_secret(client):
    schema = app.openapi()["components"]["schemas"]["CheckoutItem"]
    assert schema["properties"]["cart_item_id"]["type"] == "string"
    secret = "DoNotEchoPassword!"
    response = client.post("/api/v1/auth/register", json={"password": secret, "role": "ADMIN"})
    assert response.status_code == 422 and secret not in response.text


def test_serialization_empty_lists_and_no_content(client, accounts, goods, placed):
    from app.database import SessionFactory
    from app.models import Inventory
    from sqlalchemy import update

    from tests.fixtures import auth

    h = auth(accounts["alice"])
    data = client.get("/api/v1/orders/" + placed[0]["order_id"], headers=h).json()["data"]
    assert isinstance(data["order_id"], str) and isinstance(data["user_id"], str)
    assert data["total_amount"] == "80.00" and data["created_at"].endswith("+08:00")
    assert data["paid_at"] is None and data["payment"] is None
    for item in data["items"]:
        assert isinstance(item["id"], str) and isinstance(item["product_id"], str)
        assert re.fullmatch(r"\d+\.\d{2}", item["unit_price"])
        assert re.fullmatch(r"\d+\.\d{2}", item["line_amount"])
    empty = client.get("/api/v1/orders?status=PAID", headers=h)
    assert empty.status_code == 200 and empty.json()["data"]["items"] == []
    admin = auth(accounts["admin"])
    pid = goods[0]["id"]
    large = 9007199254740993
    with SessionFactory.begin() as s:
        s.execute(update(Inventory).where(Inventory.product_id == int(pid)).values(version=large))
    r = client.get("/api/v1/admin/inventory", headers=admin, params={"product_id": pid})
    assert r.json()["data"]["items"][0]["version"] == str(large)
    r = client.post(
        f"/api/v1/admin/inventory/{pid}/restock",
        headers=admin,
        json={"quantity": 1, "expected_version": str(large)},
    )
    assert r.status_code == 200 and r.json()["data"]["version"] == str(large + 1)
    category = client.post(
        "/api/v1/admin/categories", headers=admin, json={"name": "empty"}
    ).json()["data"]
    deleted = client.delete("/api/v1/admin/categories/" + category["id"], headers=admin)
    assert deleted.status_code == 204 and deleted.content == b""


def test_database_errors_do_not_leak_sql_or_credentials(client, accounts):
    import pymysql
    from app.database import engine
    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError

    from tests.fixtures import auth

    secret = "private-password-token-marker"

    def reject(conn, cursor, statement, parameters, context, many):
        raise OperationalError(
            "SELECT " + secret, {"password": secret}, pymysql.err.OperationalError(2013, secret)
        )

    event.listen(engine, "before_cursor_execute", reject)
    try:
        response = client.get("/api/v1/admin/users", headers=auth(accounts["admin"]))
    finally:
        event.remove(engine, "before_cursor_execute", reject)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATA_INTEGRITY_ERROR"
    assert (
        secret not in response.text
        and "SELECT" not in response.text
        and "Traceback" not in response.text
    )
