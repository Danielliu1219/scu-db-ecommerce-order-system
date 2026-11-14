import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from ..value_types import normalize
from .common import Input, NonemptyPatch


def username(value):
    if not isinstance(value, str):
        raise ValueError("Invalid username")
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", value):
        raise ValueError("Invalid username")
    return value


Name = Annotated[str, BeforeValidator(normalize), Field(min_length=1, max_length=50)]
Phone = Annotated[str, BeforeValidator(normalize), Field(min_length=1, max_length=20)]
Password = Annotated[str, Field(min_length=8, max_length=64)]


class Register(Input):
    username: Annotated[str, BeforeValidator(username)]
    password: Password
    nickname: Name
    phone: Phone


class Login(Input):
    username: Annotated[str, BeforeValidator(username)]
    password: str = Field(min_length=1, max_length=64)


class ProfilePatch(NonemptyPatch):
    nickname: Name | None = None
    phone: Phone | None = None


class PasswordChange(Input):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: Password


class UserOut(BaseModel):
    id: str
    username: str
    nickname: str
    phone: str
    role: str
    created_at: str
    updated_at: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_id: str
    role: str
