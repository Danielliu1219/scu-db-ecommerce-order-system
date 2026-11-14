from typing import Annotated

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from ..schemas.common import Pagination
from ..value_types import json_value


def pagination(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    return Pagination(page=page, page_size=page_size)


Paging = Annotated[Pagination, Depends(pagination)]


def response(data, status=200):
    return JSONResponse({"data": json_value(data)}, status_code=status)
