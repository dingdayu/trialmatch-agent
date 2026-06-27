import uuid
from typing import Any

from pydantic import BaseModel


class APIResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "success"
    data: Any = None
    request_id: str = ""

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "APIResponse":
        return cls(
            code=0,
            message=message,
            data=data,
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        )

    @classmethod
    def error(cls, code: int, message: str, data: Any = None) -> "APIResponse":
        return cls(
            code=code,
            message=message,
            data=data,
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        )
