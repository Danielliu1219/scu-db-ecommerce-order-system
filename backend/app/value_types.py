import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import BeforeValidator, PlainSerializer, StrictInt, WithJsonSchema

from .errors import fail

TZ = ZoneInfo("Asia/Shanghai")
INT_MAX = 2147483647
MAX_MONEY = Decimal("99999999.99")
OrderStatus = Literal["PENDING", "PAID", "SHIPPED", "COMPLETED", "CANCELLED"]
ProductStatus = Literal["ON_SHELF", "OFF_SHELF"]


def identifier(value):
    if (
        isinstance(value, bool)
        or not isinstance(value, (str, int))
        or not re.fullmatch(r"[0-9]+", str(value))
    ):
        raise ValueError("invalid identifier")
    result = int(value)
    if not 0 < result <= 18446744073709551615:
        raise ValueError("identifier out of range")
    return result


def version(value):
    if str(value) == "0" and not isinstance(value, bool):
        return 0
    return identifier(value)


def normalize(value):
    if not isinstance(value, str):
        raise ValueError("Text required")
    return unicodedata.normalize("NFC", value.strip())


def local_time(value, code="TIME_RANGE_INVALID"):
    try:
        result = datetime.fromisoformat(value) if isinstance(value, str) else value
        if result.microsecond:
            raise ValueError()
        return (
            result.replace(tzinfo=TZ).replace(tzinfo=None)
            if result.tzinfo is None
            else result.astimezone(TZ).replace(tzinfo=None)
        )
    except (ValueError, TypeError, AttributeError):
        fail(code, 422, "时间须为秒级ISO 8601时间")


def time_range(start, end, required=False):
    if start is None and end is None and not required:
        return None, None
    if start is None or end is None:
        fail("TIME_RANGE_INVALID", 422)
    start, end = local_time(start), local_time(end)
    if start >= end:
        fail("TIME_RANGE_INVALID", 422)
    return start, end


def money(value, code="PRICE_INVALID", zero=False):
    try:
        if isinstance(value, bool):
            raise ValueError()
        amount = Decimal(str(value))
        if (
            not amount.is_finite()
            or amount < (0 if zero else Decimal("0.01"))
            or amount > MAX_MONEY
            or amount.as_tuple().exponent < -2
        ):
            raise ValueError()
        return amount
    except (ValueError, InvalidOperation):
        fail(code, 422, "金额须在有效范围内且最多两位小数")


def json_value(value):
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, datetime):
        return value.replace(tzinfo=TZ).isoformat(timespec="seconds")
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


ID = Annotated[
    int,
    BeforeValidator(identifier),
    PlainSerializer(str, return_type=str),
    WithJsonSchema({"type": "string", "pattern": "^[0-9]+$"}),
]
Version = Annotated[
    int,
    BeforeValidator(version),
    PlainSerializer(str, return_type=str),
    WithJsonSchema({"type": "string", "pattern": "^[0-9]+$"}),
]
Quantity = Annotated[StrictInt, BeforeValidator(lambda x: x)]
