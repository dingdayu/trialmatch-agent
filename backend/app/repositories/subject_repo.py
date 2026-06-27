"""受试者数据访问层 — 对应 Task 11.2"""

from __future__ import annotations

from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.subject import Subject
from app.repositories.base_repo import BaseRepository


class SubjectRepository(BaseRepository):
    """受试者数据访问层"""
    model = Subject

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_project_and_no(
        self, project_id: str, subject_no: str
    ) -> Optional[Subject]:
        result = await self.db.execute(
            select(Subject).where(
                Subject.project_id == project_id,
                Subject.subject_no == subject_no,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        screening_status: Optional[str] = None,
        overall_result: Optional[str] = None,
        site_name: Optional[str] = None,
    ) -> Tuple[List[Subject], int]:
        query = select(Subject).where(Subject.project_id == project_id)
        count_query = (
            select(func.count())
            .select_from(Subject)
            .where(Subject.project_id == project_id)
        )

        if keyword:
            kw = or_(
                Subject.subject_no.ilike(f"%{keyword}%"),
                Subject.site_name.ilike(f"%{keyword}%"),
                Subject.diagnosis.ilike(f"%{keyword}%"),
            )
            query = query.where(kw)
            count_query = count_query.where(kw)
        if screening_status:
            query = query.where(Subject.screening_status == screening_status)
            count_query = count_query.where(Subject.screening_status == screening_status)
        if overall_result:
            query = query.where(Subject.overall_result == overall_result)
            count_query = count_query.where(Subject.overall_result == overall_result)
        if site_name:
            query = query.where(Subject.site_name == site_name)
            count_query = count_query.where(Subject.site_name == site_name)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Subject.updated_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
