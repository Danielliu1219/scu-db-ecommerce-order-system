from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .errors import register_handlers
from .schemas.common import ErrorResponse


def create_app():
    app = FastAPI(
        title="电商订单管理系统",
        version="0.1.0",
        responses={
            code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 500, 503)
        },
    )
    register_handlers(app)
    from .api import router

    app.include_router(router, prefix="/api/v1")
    dist = Path(__file__).resolve().parents[2] / "frontend/dist"
    if dist.is_dir():

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str):
            from .errors import fail

            if path == "api" or path.startswith("api/"):
                fail("RESOURCE_NOT_FOUND", 404)
            target = (dist / path).resolve()
            if target.is_relative_to(dist.resolve()) and target.is_file():
                return FileResponse(target)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
