from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from sqlalchemy.pool import StaticPool

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@event.listens_for(engine.sync_engine, "connect")
def enable_sqlite_fks(dbapi_connection, connection_record):
    """启用 SQLite 外键约束"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库：创建所有表，并对既有 SQLite 库补齐新增列"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_columns)


def _ensure_columns(sync_conn):
    """为既有表补齐模型新增列（SQLite 无法通过 create_all 添加列）"""
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    expected = {
        "eligibility_criteria": {
            "source": "VARCHAR(16) NOT NULL DEFAULT 'manual'",
            "review_status": "VARCHAR(16) NOT NULL DEFAULT 'confirmed'",
        },
    }
    for table, columns in expected.items():
        if not inspector.has_table(table):
            continue
        existing = {col["name"] for col in inspector.get_columns(table)}
        for name, ddl in columns.items():
            if name not in existing:
                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
