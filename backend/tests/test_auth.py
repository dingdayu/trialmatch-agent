"""认证模块测试 — 对应 Task 20.2"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """测试健康检查"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_detailed(client: AsyncClient):
    """测试详细健康检查"""
    response = await client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_login_invalid_user(client: AsyncClient):
    """测试登录：用户不存在"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "test123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    """测试获取当前用户：无 token"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """测试登录成功"""
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient):
    """测试获取当前用户：有 token"""
    # 先登录获取 token
    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    token = login_resp.json()["data"]["access_token"]

    response = await client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["username"] == "admin"
