"""用户数据访问层 — 对应技术设计文档 Task 4.4"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):
    """用户数据访问"""

    model = User

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_username(self, username: str) -> Optional[User]:
        """按用户名查询"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update_password(self, user_id: str, new_password_hash: str) -> None:
        """更新用户密码"""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(password_hash=new_password_hash)
        )
        await self.db.commit()
