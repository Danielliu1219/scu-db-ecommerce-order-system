from sqlalchemy import select, true
from sqlalchemy.exc import IntegrityError

from ..dependencies import require
from ..errors import fail, integrity
from ..models import Cart, User
from ..queries import page_parts
from ..security import check_password, hash_password, token
from ..transactions import constraint_name, read, sqlstate, write
from .common import contains, paged

DUMMY_HASH = hash_password("UnusedAccountTiming2026!")


def public(user):
    return {
        "id": str(user.id),
        "username": user.username,
        "nickname": user.nickname,
        "phone": user.phone,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def create(session, username, password_hash, nickname, phone, role="USER"):
    user = User(
        username=username,
        password_hash=password_hash,
        nickname=nickname,
        phone=phone,
        role=role,
    )
    session.add(user)
    session.flush()
    if role == "USER":
        session.add(Cart(user_id=user.id))
        session.flush()
    return user


def register(data):
    encoded = hash_password(data.password)
    try:
        return write(lambda s: public(create(s, data.username, encoded, data.nickname, data.phone)))
    except IntegrityError as exc:
        if sqlstate(exc) == "23505" and constraint_name(exc) == "uk_users_username":
            fail("USERNAME_EXISTS", 409, "用户名已存在")
        raise


def login(data):
    def query(s):
        user = s.scalar(select(User).where(User.username == data.username))
        valid = check_password(data.password, user.password_hash if user else DUMMY_HASH)
        if user is None or not valid:
            fail("INVALID_CREDENTIALS", 401, "用户名或密码错误")
        return {
            "access_token": token(user.id),
            "token_type": "Bearer",
            "expires_in": 7200,
            "user_id": str(user.id),
            "role": user.role,
        }

    return read(query)


def me(actor):
    def query(s):
        user = s.get(User, actor.id)
        integrity(user is not None)
        return public(user)

    return read(query)


def profile(actor, data):
    require(actor, "USER")

    def change(s):
        user = s.scalar(select(User).where(User.id == actor.id).with_for_update())
        integrity(user is not None)
        for key in data.model_fields_set:
            setattr(user, key, getattr(data, key))
        s.flush()
        s.refresh(user)
        return public(user)

    return write(change)


def password(actor, data):
    require(actor, "USER")

    def change(s):
        user = s.scalar(select(User).where(User.id == actor.id).with_for_update())
        integrity(user is not None)
        if not check_password(data.old_password, user.password_hash):
            fail("OLD_PASSWORD_INCORRECT", 400, "原密码不正确")
        user.password_hash = hash_password(data.new_password)
        s.flush()
        return {"changed": True}

    return write(change)


def users(actor, username=None, phone=None, page_number=1, page_size=20):
    require(actor, "ADMIN")

    def query(s):
        stmt = select(User.id).where(User.role == "USER")
        if username:
            stmt = stmt.where(contains(User.username, username))
        if phone:
            stmt = stmt.where(User.phone == phone.strip())
        page_rows, totals = page_parts(stmt, page_number, page_size)
        rows = s.execute(
            select(totals.c.total, User)
            .select_from(totals.outerjoin(page_rows, true()))
            .outerjoin(User, User.id == page_rows.c.id)
            .order_by(User.id)
        ).all()
        return paged(
            [public(u) for _, u in rows if u is not None], rows[0][0], page_number, page_size
        )

    return read(query)
