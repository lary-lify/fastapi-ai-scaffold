from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Unified API envelope. ``code=0`` means success, non-zero is a business error."""

    code: int = 0
    message: str = "ok"
    data: Any = None

    @classmethod
    def success(cls, data: Any = None, message: str = "ok") -> "ApiResponse":
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 1, data: Any = None) -> "ApiResponse":
        return cls(code=code, message=message, data=data)


def success_response(data: Any = None, message: str = "ok") -> dict:
    return ApiResponse.success(data=data, message=message).model_dump()


def error_response(message: str, code: int = 1, data: Any = None) -> dict:
    return ApiResponse.error(message=message, code=code, data=data).model_dump()
