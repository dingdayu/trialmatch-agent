from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.security import decode_token
from app.models.user import User
from app.exceptions import UnauthorizedException, ForbiddenException
from app.schemas.enums import UserStatus

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT 令牌中解析当前登录用户"""
    try:
        payload = decode_token(credentials.credentials)
    except ValueError:
        raise UnauthorizedException("无效的认证令牌")

    if payload.get("type") != "access":
        raise UnauthorizedException("请使用访问令牌")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("令牌中缺少用户信息")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("用户不存在")
    if user.status != UserStatus.ACTIVE:
        raise ForbiddenException("账号已被禁用")

    return user


def require_role(*allowed_roles: str):
    """权限校验依赖：检查当前用户是否拥有指定角色"""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(f"角色 {current_user.role} 无权限执行此操作")
        return current_user

    return role_checker


async def get_current_user_ws(token: str) -> User:
    """WebSocket 认证：从 URL 参数中的 token 解析用户"""
    from app.database import async_session

    try:
        payload = decode_token(token)
    except ValueError:
        raise UnauthorizedException("无效的认证令牌")

    if payload.get("type") != "access":
        raise UnauthorizedException("请使用访问令牌")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("令牌中缺少用户信息")

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedException("用户不存在")
        if user.status != UserStatus.ACTIVE:
            raise ForbiddenException("账号已被禁用")
        return user
