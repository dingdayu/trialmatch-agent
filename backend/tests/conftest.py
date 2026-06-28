"""测试基础设施 — 对应 Task 20.1
pytest fixtures：异步测试客户端、测试数据库、mock 用户"""

from __future__ import annotations

import os
import sys
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# 确保 backend 在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_db, async_session, engine, Base
from app.models.user import User
from app.utils.security import create_access_token
from app.utils.security import hash_password


@pytest.fixture(scope="session")
def event_loop():
    """创建 session 级别的事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """每个测试函数使用独立的内存数据库"""
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        session.add(User(
            username="admin",
            password_hash=hash_password("admin123"),
            display_name="系统管理员",
            role="admin",
            email="admin@trialmatch.com",
        ))
        await session.commit()

    yield

    # 清理表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(test_db):
    """提供数据库会话"""
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """提供 HTTP 测试客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def admin_token() -> str:
    """生成管理员 token"""
    return create_access_token("test-admin-id", "admin", "admin")


@pytest.fixture
def crc_token() -> str:
    """生成 CRC 用户 token"""
    return create_access_token("test-crc-id", "crc001", "crc")


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    """管理员认证头"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def crc_auth_headers(crc_token: str) -> dict:
    """CRC 认证头"""
    return {"Authorization": f"Bearer {crc_token}"}
