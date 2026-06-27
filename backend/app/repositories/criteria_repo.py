"""入排标准数据访问层 — 对应 Task 7.2"""

from __future__ import annotations

from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.criteria import EligibilityCriterion
from app.repositories.base_repo import BaseRepository


class CriteriaRepository(BaseRepository):
    """入排标准数据访问层"""
    model = EligibilityCriterion

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def list_by_project(
        self,
        project_id: str,
        criterion_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[EligibilityCriterion]:
        query = select(EligibilityCriterion).where(
            EligibilityCriterion.project_id == project_id
        )
        if criterion_type:
            query = query.where(EligibilityCriterion.criterion_type == criterion_type)
        if is_active is not None:
            query = query.where(EligibilityCriterion.is_active == is_active)

        query = query.order_by(EligibilityCriterion.sort_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_project_and_code(
        self, project_id: str, criterion_code: str
    ) -> Optional[EligibilityCriterion]:
        result = await self.db.execute(
            select(EligibilityCriterion).where(
                EligibilityCriterion.project_id == project_id,
                EligibilityCriterion.criterion_code == criterion_code,
            )
        )
        return result.scalar_one_or_none()
