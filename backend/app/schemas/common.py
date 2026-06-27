"""统一响应格式与错误码 — 对应技术设计文档第 3.1-3.2 节"""

import uuid
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field


# ========== 错误码枚举 ==========

class ErrorCode:
    """全局错误码"""
    SUCCESS = 0
    # 通用
    BAD_REQUEST = 40001
    VALIDATION_ERROR = 40002
    # 认证
    UNAUTHORIZED = 40101
    TOKEN_EXPIRED = 40102
    TOKEN_INVALID = 40103
    # 权限
    FORBIDDEN = 40301
    ROLE_NOT_ALLOWED = 40302
    ACCOUNT_DISABLED = 40303
    # 资源
    NOT_FOUND = 40401
    # 冲突
    CONFLICT = 40901
    RESOURCE_IN_USE = 40902
    # 限流
    RATE_LIMITED = 42901
    # 服务端
    INTERNAL_ERROR = 50001
    DATABASE_ERROR = 50002
    AI_ENGINE_ERROR = 50003
    # 外部服务
    SERVICE_UNAVAILABLE = 50301


# 错误码对应的默认消息
ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.BAD_REQUEST: "请求参数有误",
    ErrorCode.VALIDATION_ERROR: "数据校验失败",
    ErrorCode.UNAUTHORIZED: "未登录或登录已过期",
    ErrorCode.TOKEN_EXPIRED: "令牌已过期",
    ErrorCode.TOKEN_INVALID: "无效的令牌",
    ErrorCode.FORBIDDEN: "无权限访问",
    ErrorCode.ROLE_NOT_ALLOWED: "当前角色无权限执行此操作",
    ErrorCode.ACCOUNT_DISABLED: "账号已被禁用",
    ErrorCode.NOT_FOUND: "请求的资源不存在",
    ErrorCode.CONFLICT: "资源冲突",
    ErrorCode.RESOURCE_IN_USE: "资源正在使用中，无法删除",
    ErrorCode.RATE_LIMITED: "请求过于频繁，请稍后再试",
    ErrorCode.INTERNAL_ERROR: "服务器内部错误",
    ErrorCode.DATABASE_ERROR: "数据库操作异常",
    ErrorCode.AI_ENGINE_ERROR: "AI 引擎调用异常",
    ErrorCode.SERVICE_UNAVAILABLE: "外部服务不可用",
}


# ========== 统一响应模型 ==========

T = TypeVar("T")


class APIResponse(BaseModel):
    """统一 API 响应格式（非分页）"""
    code: int = Field(default=ErrorCode.SUCCESS, description="状态码，0 表示成功")
    message: str = Field(default="success", description="提示信息")
    data: Any = Field(default=None, description="响应数据")
    request_id: str = Field(default="", description="请求追踪 ID")

    @classmethod
    def success(cls, data: Any = None, message: str = "success") -> "APIResponse":
        return cls(
            code=ErrorCode.SUCCESS,
            message=message,
            data=data,
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        )

    @classmethod
    def error(
        cls,
        code: int,
        message: Optional[str] = None,
        data: Any = None,
    ) -> "APIResponse":
        return cls(
            code=code,
            message=message or ERROR_MESSAGES.get(code, "未知错误"),
            data=data,
            request_id=f"req_{uuid.uuid4().hex[:12]}",
        )


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: list = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总条数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")


class PaginatedAPIResponse(APIResponse):
    """分页 API 响应（data 使用 PaginatedResponse 结构）"""
    data: PaginatedResponse = Field(default_factory=PaginatedResponse)
