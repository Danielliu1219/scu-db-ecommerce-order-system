from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException


class BusinessError(Exception):
    def __init__(self, code, status=409, message=None, details=None):
        self.code, self.status = code, status
        self.message, self.details = message or code, details
        super().__init__(self.message)


def fail(code, status=409, message=None, details=None):
    raise BusinessError(code, status, message, details)


def integrity(condition, message="业务数据完整性检查失败"):
    if not condition:
        fail("DATA_INTEGRITY_ERROR", 500, message)


def register_handlers(app):
    @app.exception_handler(BusinessError)
    async def business(_: Request, exc: BusinessError):
        error = {"code": exc.code, "message": exc.message}
        if exc.details is not None:
            error["details"] = exc.details
        return JSONResponse({"error": error}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation(_: Request, exc: RequestValidationError):
        # Never echo request input: validation may involve a password or token.
        details = [
            {"field": ".".join(map(str, e["loc"])), "reason": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(
            {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "请求格式不正确",
                    "details": details,
                }
            },
            status_code=422,
        )

    @app.exception_handler(SQLAlchemyError)
    async def database(_: Request, exc: SQLAlchemyError):
        return JSONResponse(
            {"error": {"code": "DATA_INTEGRITY_ERROR", "message": "数据库操作未完成"}},
            status_code=500,
        )

    @app.exception_handler(HTTPException)
    async def http(_: Request, exc: HTTPException):
        code = "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "VALIDATION_ERROR"
        return JSONResponse(
            {"error": {"code": code, "message": "请求无法处理"}},
            status_code=exc.status_code,
        )
