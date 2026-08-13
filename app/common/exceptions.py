from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.response import error_response
from app.config.setting import settings


class BusinessError(Exception):
    """Domain error carrying a code + message, rendered as a unified response."""

    def __init__(self, message: str = "业务异常", code: int = 1):
        self.message = message
        self.code = code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def _business_error_handler(request: Request, exc: BusinessError):
        return JSONResponse(status_code=200, content=error_response(exc.message, exc.code))

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_response("请求参数校验失败", code=422, data=exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(str(exc.detail), code=exc.status_code),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception):
        # Never leak internal exception text in production.
        detail = "服务器内部错误"
        if settings.app.env != "prod":
            detail = f"服务器内部错误: {exc}"
        return JSONResponse(status_code=500, content=error_response(detail, code=500))
