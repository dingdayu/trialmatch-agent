from __future__ import annotations

from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.project import Project


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_projects(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None,
    ) -> Tuple[List[Project], int]:
        """获取项目列表（分页、筛选）"""
        query = select(Project)
        count_query = select(func.count()).select_from(Project)

        if keyword:
            keyword_filter = or_(
                Project.project_no.ilike(f"%{keyword}%"),
                Project.study_name.ilike(f"%{keyword}%"),
                Project.indication.ilike(f"%{keyword}%"),
            )
            query = query.where(keyword_filter)
            count_query = count_query.where(keyword_filter)

        if status:
            query = query.where(Project.status == status)
            count_query = count_query.where(Project.status == status)

        if phase:
            query = query.where(Project.phase == phase)
            count_query = count_query.where(Project.phase == phase)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Project.updated_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_project(self, project_id: str) -> Project:
        """获取项目详情"""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        return project

    async def create_project(self, data: dict, user_id: str) -> Project:
        """创建新项目"""
        existing = await self.db.execute(
            select(Project).where(Project.project_no == data["project_no"])
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"项目编号 {data['project_no']} 已存在")

        project = Project(**data, created_by=user_id)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update_project(self, project_id: str, data: dict) -> Project:
        """更新项目"""
        project = await self.get_project(project_id)
        for key, value in data.items():
            if value is not None and hasattr(project, key):
                setattr(project, key, value)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: str) -> None:
        """删除项目"""
        project = await self.get_project(project_id)
        # 检查是否存在受试者数据
        from app.models.subject import Subject
        result = await self.db.execute(
            select(func.count()).select_from(Subject).where(Subject.project_id == project_id)
        )
        subject_count = result.scalar() or 0
        if subject_count > 0:
            raise ValueError(f"项目下存在 {subject_count} 名受试者，无法删除")
        await self.db.delete(project)
        await self.db.commit()
