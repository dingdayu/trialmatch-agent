from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import DeclarativeBase


class BaseRepository:
    """通用 Repository 基类"""

    model: type[DeclarativeBase]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: str):
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)  # type: ignore
        )
        return result.scalar_one_or_none()

    async def get_all(self, page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        count_query = select(func.count()).select_from(self.model)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = select(self.model).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total, page, page_size

    async def create(self, obj):
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj, **kwargs):
        for key, value in kwargs.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj):
        await self.db.delete(obj)
        await self.db.commit()
