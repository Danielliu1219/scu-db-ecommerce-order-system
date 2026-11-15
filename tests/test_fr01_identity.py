import pytest
from app.database import SessionFactory
from app.models import Cart, User
from app.schemas.identity import Register
from app.services import identity
from sqlalchemy import func, select

from tests.fixtures import PASSWORD, auth

BASE = "/api/v1"
REG = {
    "username": "  Alice_1 ",
    "password": PASSWORD,
    "nickname": "同学",
    "phone": "00123",
}


def test_register_login_profile_password(client):
    r = client.post(BASE + "/auth/register", json=REG)
    assert r.status_code == 201, r.text
    user = r.json()["data"]
    assert user["username"] == "alice_1" and isinstance(user["id"], str)
    assert "password_hash" not in user and user["created_at"].endswith("+08:00")
    with SessionFactory() as s:
        assert s.scalar(select(func.count()).select_from(Cart)) == 1
        assert s.get(User, int(user["id"])).password_hash.startswith("$argon2id$")
    assert (
        client.post(BASE + "/auth/register", json=REG).json()["error"]["code"] == "USERNAME_EXISTS"
    )
    r = client.post(BASE + "/auth/login", json={"username": " ALICE_1 ", "password": PASSWORD})
    assert r.status_code == 200
    headers = {"Authorization": "Bearer " + r.json()["data"]["access_token"]}
    assert (
        client.patch(BASE + "/users/me", headers=headers, json={"nickname": "新名字"}).json()[
            "data"
        ]["nickname"]
        == "新名字"
    )
    assert (
        client.put(
            BASE + "/users/me/password",
            headers=headers,
            json={"old_password": "wrong", "new_password": "Another2026!"},
        ).status_code
        == 400
    )
    assert (
        client.put(
            BASE + "/users/me/password",
            headers=headers,
            json={"old_password": PASSWORD, "new_password": "Another2026!"},
        ).status_code
        == 200
    )
    assert client.get(BASE + "/users/me", headers=headers).status_code == 200


@pytest.mark.parametrize(
    "changes",
    [
        {"role": "ADMIN"},
        {"password": "short"},
        {"username": "用户名"},
        {"nickname": "   "},
    ],
)
def test_registration_rejects_invalid_or_extra_fields(client, changes):
    assert client.post(BASE + "/auth/register", json=REG | changes).status_code == 422


def test_roles_and_user_query(client, accounts):
    admin, alice = accounts["admin"], accounts["alice"]
    assert client.get(BASE + "/users/me").status_code == 401
    assert client.get(BASE + "/admin/users", headers=auth(alice)).status_code == 403
    assert (
        client.patch(BASE + "/users/me", headers=auth(admin), json={"nickname": "x"}).status_code
        == 403
    )
    assert client.get(BASE + "/admin/users", headers=auth(admin)).json()["data"]["total"] == 2
    with SessionFactory() as s:
        assert s.scalar(select(Cart).where(Cart.user_id == admin.id)) is None


def test_cart_insert_failure_rolls_back_user(monkeypatch):
    from sqlalchemy import event

    def reject(*args):
        raise RuntimeError("injected cart failure")

    event.listen(Cart, "before_insert", reject)
    try:
        with pytest.raises(RuntimeError):
            identity.register(Register(**REG))
    finally:
        event.remove(Cart, "before_insert", reject)
    with SessionFactory() as s:
        assert s.scalar(select(User).where(User.username == "alice_1")) is None
