from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from .config import settings

passwords = PasswordHash.recommended()


def hash_password(password):
    return passwords.hash(password)


def check_password(password, encoded):
    return passwords.verify(password, encoded)


def token(user_id):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(seconds=7200)},
        settings().jwt_secret,
        algorithm="HS256",
    )
