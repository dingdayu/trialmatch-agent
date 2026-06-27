"""
TrialMatch AI 公共依赖注入模块

提供数据库会话、用户认证、权限校验等公共依赖
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session


# ============================================
# 数据库会话依赖
# ============================================

async def get_db() -> AsyncSession:
    """
    获取数据库会话
    用于 FastAPI 的 Depends()
    """
    async for session in get_db_session():
        yield session


# ============================================
# 权限依赖
# ============================================

def require_role(*allowed_roles: str) -> Callable:
    """
    权限校验依赖工厂

    用法:
        @router.get("/admin-only")
        async def admin_endpoint(user = Depends(require_role("admin"))):
            ...

    Args:
        *allowed_roles: 允许访问的角色列表

    Returns:
        FastAPI 依赖函数
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": 40301,
                    "message": f"角色 {current_user.get('role')} 无权限执行此操作",
                },
            )
        return current_user

    return role_checker


# ============================================
# 用户认证依赖（占位，Task 4 实现）
# ============================================

async def get_current_user() -> dict:
    """
    获取当前用户（占位实现）

    TODO: Task 4 将实现完整的 JWT 解析逻辑
    """
    # 占位返回，Task 4 会替换为真实的 JWT 解析
    return {
        "id": "placeholder-user-id",
        "username": "placeholder",
        "role": "admin",
    }
