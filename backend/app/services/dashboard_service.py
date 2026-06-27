"""项目统计服务 — 对应 Task 16.1"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.project import Project
from app.models.subject import Subject
from app.models.file import UploadedFile
from app.models.screening_run import ScreeningRun
from app.models.evaluation import CriterionEvaluation


class DashboardService:
    """仪表盘统计服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_overview(self, project_id: str) -> dict:
        """获取项目概览统计 — 接口 #48"""
        # 受试者统计
        subject_count = await self._count(Subject, Subject.project_id == project_id)
        
        # 各状态受试者
        screened_count = await self._count(
            Subject,
            Subject.project_id == project_id,
            Subject.screening_status == "screened",
        )
        pending_count = await self._count(
            Subject,
            Subject.project_id == project_id,
            Subject.screening_status.in_(["pending", "screening"]),
        )

        # 各结论统计
        recommended_count = await self._count(
            Subject,
            Subject.project_id == project_id,
            Subject.overall_result == "recommended",
        )
        excluded_count = await self._count(
            Subject,
            Subject.project_id == project_id,
            Subject.overall_result == "excluded",
        )
        manual_review_count = await self._count(
            Subject,
            Subject.project_id == project_id,
            Subject.overall_result == "manual_review",
        )

        # 文件统计
        file_count = await self._count(UploadedFile, UploadedFile.project_id == project_id)
        parsed_count = await self._count(
            UploadedFile,
            UploadedFile.project_id == project_id,
            UploadedFile.parse_status == "completed",
        )

        # AI 任务统计
        total_runs = await self._count(ScreeningRun, ScreeningRun.project_id == project_id)
        completed_runs = await self._count(
            ScreeningRun,
            ScreeningRun.project_id == project_id,
            ScreeningRun.status == "completed",
        )
        failed_runs = await self._count(
            ScreeningRun,
            ScreeningRun.project_id == project_id,
            ScreeningRun.status == "failed",
        )

        # 平均耗时
        avg_duration = await self._get_avg_duration(project_id)

        return {
            "project_id": project_id,
            "subject_count": subject_count,
            "screened_count": screened_count,
            "pending_count": pending_count,
            "recommended_count": recommended_count,
            "excluded_count": excluded_count,
            "manual_review_count": manual_review_count,
            "file_count": file_count,
            "parsed_file_count": parsed_count,
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "average_duration_seconds": avg_duration,
        }

    async def get_screening_stats(self, project_id: Optional[str] = None) -> dict:
        """获取 AI 任务统计 — 接口 #49"""
        query = select(ScreeningRun)
        if project_id:
            query = query.where(ScreeningRun.project_id == project_id)

        result = await self.db.execute(query)
        runs = list(result.scalars().all())

        status_counts = {"queued": 0, "running": 0, "completed": 0, "failed": 0}
        total_duration = 0.0
        completed = 0

        for run in runs:
            status_counts[run.status] = status_counts.get(run.status, 0) + 1
            if run.started_at and run.completed_at:
                duration = (run.completed_at - run.started_at).total_seconds()
                total_duration += duration
                completed += 1

        return {
            **status_counts,
            "total": len(runs),
            "average_duration_seconds": round(total_duration / completed, 1) if completed > 0 else 0,
        }

    async def _count(self, model, *filters) -> int:
        query = select(func.count()).select_from(model)
        for f in filters:
            query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def _get_avg_duration(self, project_id: str) -> float:
        result = await self.db.execute(
            select(func.avg(
                func.julianday(ScreeningRun.completed_at) - func.julianday(ScreeningRun.started_at)
            )).where(
                ScreeningRun.project_id == project_id,
                ScreeningRun.status == "completed",
                ScreeningRun.started_at.isnot(None),
                ScreeningRun.completed_at.isnot(None),
            )
        )
        avg = result.scalar()
        if avg:
            return round(avg * 86400, 1)  # 转换为秒
        return 0.0
