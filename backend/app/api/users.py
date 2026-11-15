from fastapi import APIRouter

from ..dependencies import Actor
from ..schemas.common import Changed, Page, Response
from ..schemas.identity import PasswordChange, ProfilePatch, UserOut
from ..services import identity
from .common import Paging, response

router = APIRouter(tags=["FR-01 用户"])


@router.get("/users/me", response_model=Response[UserOut])
def me(actor: Actor):
    return response(identity.me(actor))


@router.patch("/users/me", response_model=Response[UserOut])
def profile(actor: Actor, data: ProfilePatch):
    return response(identity.profile(actor, data))


@router.put("/users/me/password", response_model=Response[Changed])
def password(actor: Actor, data: PasswordChange):
    return response(identity.password(actor, data))


@router.get("/admin/users", response_model=Response[Page[UserOut]])
def users(actor: Actor, paging: Paging, username: str | None = None, phone: str | None = None):
    return response(identity.users(actor, username, phone, paging.page, paging.page_size))
