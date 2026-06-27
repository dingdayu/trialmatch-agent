from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class UserCreate(BaseModel):
    """创建用户（管理后台用）"""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=128)
    role: str = Field(default="crc")
    email: Optional[str] = Field(None, max_length=256)


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    display_name: str
    role: str
    email: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT 令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
