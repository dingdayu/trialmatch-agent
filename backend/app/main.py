import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, async_session
from app.api.router import router as api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库 + 创建默认管理员"""
    # 确保 resource 目录存在
    os.makedirs(settings.upload_dir, exist_ok=True)

    # 创建数据库表
    await init_db()

    # 创建默认管理员账号（如果不存在）
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
                role="admin",
                email="admin@trialmatch.com",
            )
            db.add(admin)

            crc = User(
                username="crc001",
                password_hash=hash_password("123456"),
                display_name="CRC 用户",
                role="crc",
                email="crc001@example.com",
            )
            db.add(crc)

            pm = User(
                username="pm001",
                password_hash=hash_password("123456"),
                display_name="项目管理员",
                role="project_manager",
                email="pm001@example.com",
            )
            db.add(pm)

            await db.commit()
            print("✅ 已创建默认账号: admin/admin123, crc001/123456, pm001/123456")

    print(f"✅ {settings.app_name} v{settings.app_version} 启动成功")
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS 配置（开发阶段允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}
