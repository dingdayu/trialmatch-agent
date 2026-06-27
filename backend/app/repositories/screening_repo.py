"""初筛数据访问层 — 对应 Task 12.2"""

from __future__ import annotations

from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.screening_run import ScreeningRun


class ScreeningRunRepository:
    """初筛任务数据访问层"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, run_id: str) -> Optional[ScreeningRun]:
        result = await self.db.execute(
            select(ScreeningRun).where(ScreeningRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_by_subject(
        self,
        subject_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ScreeningRun], int]:
        query = select(ScreeningRun).where(ScreeningRun.subject_id == subject_id)
        count_query = select(func.count()).select_from(ScreeningRun).where(
            ScreeningRun.subject_id == subject_id
        )

        if status:
            query = query.where(ScreeningRun.status == status)
            count_query = count_query.where(ScreeningRun.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(ScreeningRun.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_latest_completed(self, subject_id: str) -> Optional[ScreeningRun]:
        result = await self.db.execute(
            select(ScreeningRun)
            .where(ScreeningRun.subject_id == subject_id, ScreeningRun.status == "completed")
            .order_by(ScreeningRun.completed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_stats_by_status(self, project_id: Optional[str] = None) -> dict:
        query = select(ScreeningRun.status, func.count()).group_by(ScreeningRun.status)
        if project_id:
            query = query.where(ScreeningRun.project_id == project_id)

        result = await self.db.execute(query)
        stats = {"queued": 0, "running": 0, "completed": 0, "failed": 0}
        for status, count in result.all():
            stats[status] = count
        stats["total"] = sum(stats.values())
        return stats
