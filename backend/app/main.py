import os
import uuid
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.database import init_db, async_session
from app.api.router import router as api_router
from app.exceptions import AppException
from app.schemas.common import APIResponse, ErrorCode
from app.schemas.enums import UserRole
from app.utils.logger import logger

settings = get_settings()


# ========== Request ID 中间件 (Task 3.5) ==========

class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求生成唯一 request_id，注入到响应体"""

    async def dispatch(self, request: Request, call_next):
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ========== 应用生命周期 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库 + 创建默认账号"""
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 创建数据库表
    await init_db()

    # 创建默认账号（如果不存在）
    from app.models.user import User
    from app.utils.security import hash_password
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                display_name="系统管理员",
                role=UserRole.ADMIN,
                email="admin@trialmatch.com",
            )
            db.add(admin)

            crc = User(
                username="crc001",
                password_hash=hash_password("123456"),
                display_name="CRC 用户",
                role=UserRole.CRC,
                email="crc001@example.com",
            )
            db.add(crc)

            pm = User(
                username="pm001",
                password_hash=hash_password("123456"),
                display_name="项目管理员",
                role=UserRole.PROJECT_MANAGER,
                email="pm001@example.com",
            )
            db.add(pm)

            await db.commit()
            logger.info("已创建默认账号: admin/admin123, crc001/123456, pm001/123456")

    logger.info(f"{settings.app_name} v{settings.app_version} 启动成功")
    yield
    logger.info(f"{settings.app_name} 正在关闭")


# ========== FastAPI 应用 ==========

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID 中间件
app.add_middleware(RequestIDMiddleware)


# ========== 全局异常处理器 (Task 3.4) ==========

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """处理应用自定义异常，返回统一错误响应"""
    logger.warning(
        f"[{exc.code}] {exc.message}",
        extra={"request_id": getattr(request.state, "request_id", "")},
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=APIResponse.error(
            code=exc.code,
            message=exc.message,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底异常处理"""
    logger.error(
        f"未捕获异常: {str(exc)}",
        exc_info=True,
        extra={"request_id": getattr(request.state, "request_id", "")},
    )
    return JSONResponse(
        status_code=500,
        content=APIResponse.error(
            code=ErrorCode.INTERNAL_ERROR,
            message="服务器内部错误",
        ).model_dump(),
    )


# 注册路由
app.include_router(api_router)


# ========== 健康检查 (Task 19.1, 19.2) ==========

@app.get("/health")
async def health_check():
    """基础健康检查"""
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_check_detailed():
    """详细健康检查"""
    health = {
        "status": "ok",
        "version": settings.app_version,
        "database": "unknown",
    }
    try:
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health

