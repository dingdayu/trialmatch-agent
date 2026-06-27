from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, username: str, password: str) -> dict:
        """用户登录，返回 JWT 令牌对"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户名或密码错误")

        if not verify_password(password, user.password_hash):
            raise ValueError("用户名或密码错误")

        if user.status != "active":
            raise PermissionError("账号已被禁用，请联系管理员")

        access_token = create_access_token(user.id, user.username, user.role)
        refresh_token = create_refresh_token(user.id, user.username)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
                "email": user.email,
            },
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """刷新访问令牌"""
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise ValueError("无效的刷新令牌")

        if payload.get("type") != "refresh":
            raise ValueError("请使用刷新令牌")

        user_id = payload.get("sub")
        username = payload.get("username", "")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or user.status != "active":
            raise ValueError("用户不存在或已被禁用")

        new_access = create_access_token(user.id, user.username, user.role)
        new_refresh = create_refresh_token(user.id, user.username)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": 86400,
        }

    async def create_user(self, username: str, password: str, display_name: str,
                          role: str = "crc", email: Optional[str] = None) -> User:
        """创建新用户"""
        existing = await self.db.execute(
            select(User).where(User.username == username)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"用户名 {username} 已存在")

        user = User(
            username=username,
            password_hash=hash_password(password),
            display_name=display_name,
            role=role,
            email=email,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        """修改密码"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("用户不存在")

        if not verify_password(old_password, user.password_hash):
            raise ValueError("原密码错误")

        if old_password == new_password:
            raise ValueError("新密码不能与原密码相同")

        user.password_hash = hash_password(new_password)
        await self.db.commit()
