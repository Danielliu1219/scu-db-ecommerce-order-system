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
