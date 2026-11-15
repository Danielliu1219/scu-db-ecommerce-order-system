from fastapi import APIRouter

from ..schemas.common import Response
from ..schemas.identity import Login, LoginOut, Register, UserOut
from ..services import identity
from .common import response

router = APIRouter(tags=["FR-01 身份"])


@router.post("/auth/register", status_code=201, response_model=Response[UserOut])
def register(data: Register):
    return response(identity.register(data), 201)


@router.post("/auth/login", response_model=Response[LoginOut])
def login(data: Login):
    return response(identity.login(data))
