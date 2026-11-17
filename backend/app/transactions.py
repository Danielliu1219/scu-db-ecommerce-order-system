import random
import time

from sqlalchemy.exc import DBAPIError

from .database import SessionFactory
from .errors import fail


def sqlstate(exc):
    return getattr(getattr(exc, "orig", exc), "sqlstate", None)


def constraint_name(exc):
    return getattr(getattr(getattr(exc, "orig", exc), "diag", None), "constraint_name", None)


def read(operation):
    with SessionFactory() as session:
        return operation(session)


def write(operation, resolve_unknown=None):
    """Retry only a fully rolled-back transaction; never reuse an ORM session."""
    for attempt in range(3):
        committing = False
        try:
            with SessionFactory() as session:
                try:
                    session.begin()
                    result = operation(session)
                    committing = True
                    session.commit()
                    return result
                except Exception:
                    session.rollback()
                    raise
        except DBAPIError as exc:
            code = sqlstate(exc)
            if code in ("55P03", "40P01", "40001"):
                if attempt < 2:
                    time.sleep((0.05, 0.15)[attempt] + random.uniform(0, 0.05))
                    continue
                fail("TRANSACTION_RETRY_EXHAUSTED", 503, "事务繁忙，请稍后重试")
            if committing and (
                exc.connection_invalidated
                or (code or "").startswith("08")
                or code in ("57P01", "57P02", "57P03")
            ):
                # A fresh connection checks the committed fact before any replay.
                if resolve_unknown:
                    try:
                        resolved = read(resolve_unknown)
                        if resolved is not None:
                            return resolved
                    except DBAPIError:
                        pass
                fail(
                    "TRANSACTION_RETRY_EXHAUSTED",
                    503,
                    "提交结果待确认，请刷新核对",
                    {"outcome": "UNKNOWN"},
                )
            raise
