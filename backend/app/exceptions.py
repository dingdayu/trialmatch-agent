"""全局异常类 — 对应技术设计文档第 3.3 节"""

from typing import Optional

from app.schemas.common import ErrorCode


class AppException(Exception):
    """应用基础异常"""
    code: int = ErrorCode.INTERNAL_ERROR
    message: str = "服务器内部错误"
    http_status: int = 500

    def __init__(self, message: Optional[str] = None, code: Optional[int] = None):
        if code is not None:
            self.code = code
        if message is not None:
            self.message = message
        super().__init__(self.message)


class BadRequestException(AppException):
    """请求参数有误 (400)"""
    code = ErrorCode.BAD_REQUEST
    message = "请求参数有误"
    http_status = 400


class ValidationException(AppException):
    """数据校验失败 (400)"""
    code = ErrorCode.VALIDATION_ERROR
    message = "数据校验失败"
    http_status = 400


class UnauthorizedException(AppException):
    """未登录或登录已过期 (401)"""
    code = ErrorCode.UNAUTHORIZED
    message = "未登录或登录已过期"
    http_status = 401


class TokenExpiredException(AppException):
    """令牌已过期 (401)"""
    code = ErrorCode.TOKEN_EXPIRED
    message = "令牌已过期"
    http_status = 401


class TokenInvalidException(AppException):
    """无效的令牌 (401)"""
    code = ErrorCode.TOKEN_INVALID
    message = "无效的令牌"
    http_status = 401


class ForbiddenException(AppException):
    """无权限访问 (403)"""
    code = ErrorCode.FORBIDDEN
    message = "无权限访问"
    http_status = 403


class NotFoundException(AppException):
    """资源不存在 (404)"""
    code = ErrorCode.NOT_FOUND
    message = "请求的资源不存在"
    http_status = 404


class ConflictException(AppException):
    """资源冲突 (409)"""
    code = ErrorCode.CONFLICT
    message = "资源冲突"
    http_status = 409


class ResourceInUseException(AppException):
    """资源正在使用中 (409)"""
    code = ErrorCode.RESOURCE_IN_USE
    message = "资源正在使用中，无法删除"
    http_status = 409


class RateLimitedException(AppException):
    """请求限流 (429)"""
    code = ErrorCode.RATE_LIMITED
    message = "请求过于频繁，请稍后再试"
    http_status = 429


class DatabaseException(AppException):
    """数据库操作异常 (500)"""
    code = ErrorCode.DATABASE_ERROR
    message = "数据库操作异常"
    http_status = 500


class AIEngineException(AppException):
    """AI 引擎调用异常 (500)"""
    code = ErrorCode.AI_ENGINE_ERROR
    message = "AI 引擎调用异常"
    http_status = 500


class ServiceUnavailableException(AppException):
    """外部服务不可用 (503)"""
    code = ErrorCode.SERVICE_UNAVAILABLE
    message = "外部服务不可用"
    http_status = 503
