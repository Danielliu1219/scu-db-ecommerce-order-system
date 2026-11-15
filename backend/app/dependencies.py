from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .errors import fail
from .models import User
from .transactions import read
from .value_types import identifier

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    id: int
    role: str


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    if not credentials:
        fail("UNAUTHENTICATED", 401)
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings().jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        user_id = identifier(claims["sub"])
    except (jwt.InvalidTokenError, ValueError):
        fail("UNAUTHENTICATED", 401)
    result = read(lambda s: Principal(u.id, u.role) if (u := s.get(User, user_id)) else None)
    if result is None:
        fail("UNAUTHENTICATED", 401)
    return result


Actor = Annotated[Principal, Depends(current_user)]


def optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    authorization: Annotated[str | None, Header()] = None,
):
    if authorization is None:
        return None
    return current_user(credentials)


Visitor = Annotated[Principal | None, Depends(optional_user)]


def require(actor, role):
    if actor is None:
        fail("UNAUTHENTICATED", 401)
    if actor.role != role:
        fail("ROLE_FORBIDDEN", 403)
