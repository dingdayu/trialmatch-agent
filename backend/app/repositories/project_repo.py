"""项目数据访问层 — 对应 Task 6.2"""

from __future__ import annotations

from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.project import Project
from app.repositories.base_repo import BaseRepository


class ProjectRepository(BaseRepository):
    """项目数据访问层"""
    model = Project

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_project_no(self, project_no: str) -> Optional[Project]:
        result = await self.db.execute(
            select(Project).where(Project.project_no == project_no)
        )
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Project], int]:
        query = select(Project)
        count_query = select(func.count()).select_from(Project)

        if keyword:
            kw_filter = or_(
                Project.project_no.ilike(f"%{keyword}%"),
                Project.study_name.ilike(f"%{keyword}%"),
                Project.indication.ilike(f"%{keyword}%"),
            )
            query = query.where(kw_filter)
            count_query = count_query.where(kw_filter)
        if status:
            query = query.where(Project.status == status)
            count_query = count_query.where(Project.status == status)
        if phase:
            query = query.where(Project.phase == phase)
            count_query = count_query.where(Project.phase == phase)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        sort_col = getattr(Project, sort_by, Project.updated_at)
        if sort_order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
