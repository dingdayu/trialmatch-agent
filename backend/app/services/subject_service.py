from __future__ import annotations

from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.subject import Subject


class SubjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_subjects(
        self,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        screening_status: Optional[str] = None,
        overall_result: Optional[str] = None,
        site_name: Optional[str] = None,
    ) -> Tuple[List[Subject], int]:
        """获取受试者列表"""
        query = select(Subject).where(Subject.project_id == project_id)
        count_query = (
            select(func.count())
            .select_from(Subject)
            .where(Subject.project_id == project_id)
        )

        if keyword:
            keyword_filter = or_(
                Subject.subject_no.ilike(f"%{keyword}%"),
                Subject.site_name.ilike(f"%{keyword}%"),
                Subject.diagnosis.ilike(f"%{keyword}%"),
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

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

    async def get_subject(self, subject_id: str) -> Subject:
        """获取受试者详情"""
        result = await self.db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise ValueError(f"受试者 {subject_id} 不存在")
        return subject

    async def create_subject(self, project_id: str, data: dict, user_id: str) -> Subject:
        """新增受试者"""
        existing = await self.db.execute(
            select(Subject).where(
                Subject.project_id == project_id,
                Subject.subject_no == data["subject_no"],
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"受试者编号 {data['subject_no']} 在当前项目中已存在")

        subject = Subject(project_id=project_id, created_by=user_id, **data)
        self.db.add(subject)
        await self.db.commit()
        await self.db.refresh(subject)
        return subject

    async def update_subject(self, subject_id: str, data: dict) -> Subject:
        """更新受试者"""
        subject = await self.get_subject(subject_id)
        for key, value in data.items():
            if value is not None and hasattr(subject, key):
                setattr(subject, key, value)
        await self.db.commit()
        await self.db.refresh(subject)
        return subject

    async def delete_subject(self, subject_id: str) -> None:
        """删除受试者"""
        subject = await self.get_subject(subject_id)
        await self.db.delete(subject)
        await self.db.commit()
