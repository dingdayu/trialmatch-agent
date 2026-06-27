"""向后兼容：从 common.py 重新导出 APIResponse"""

from app.schemas.common import APIResponse, PaginatedResponse, PaginatedAPIResponse, ErrorCode, ERROR_MESSAGES

__all__ = ["APIResponse", "PaginatedResponse", "PaginatedAPIResponse", "ErrorCode", "ERROR_MESSAGES"]
