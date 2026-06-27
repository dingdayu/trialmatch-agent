"""
TrialMatch AI FastAPI 应用入口

提供应用实例、中间件注册、路由挂载、生命周期管理
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_db, init_db
from app.api.router import api_v1_router


# ============================================
# 生命周期管理
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    await init_db()
    yield
    # 关闭时执行
    await close_db()


# ============================================
# 创建 FastAPI 应用
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 辅助临床研究受试者初筛与证据溯源系统",
    lifespan=lifespan,
)


# ============================================
# 中间件注册
# ============================================

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Request ID 中间件
# ============================================

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """为每个请求生成唯一 request_id"""
    # 生成 request_id
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    request_id = f"req_{timestamp}_{unique_id}"

    # 存储到 request.state 供后续使用
    request.state.request_id = request_id

    # 处理请求
    response = await call_next(request)

    # 在响应头中添加 request_id
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================
# 全局异常处理器（Task 3 完善）
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    request_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=500,
        content={
            "code": 50001,
            "message": "服务器内部错误",
            "data": None,
            "request_id": request_id,
        },
    )


# ============================================
# 注册路由
# ============================================

app.include_router(api_v1_router)


# ============================================
# 健康检查端点
# ============================================

@app.get("/health", tags=["系统"])
async def health_check():
    """基础健康检查"""
    return {"status": "ok"}


@app.get("/health/detailed", tags=["系统"])
async def detailed_health_check():
    """详细健康检查"""
    # TODO: Task 19 实现完整的健康检查逻辑
    return {
        "status": "ok",
        "checks": {
            "database": {"status": "ok"},
            "redis": {"status": "ok"},
            "llm": {"status": "ok"},
        },
    }


# ============================================
# 根路径
# ============================================

@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
