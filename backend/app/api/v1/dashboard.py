"""仪表盘 API — 对应 Task 16.2-16.3, 接口 #48-#49"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.services.dashboard_service import DashboardService
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("/dashboard")
async def project_overview(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#48 项目概览统计"""
    service = DashboardService(db)
    data = await service.get_project_overview(project_id)
    return APIResponse.success(data=data)


@router.get("/screening-runs/stats")
async def screening_stats(
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#49 AI 任务统计"""
    service = DashboardService(db)
    data = await service.get_screening_stats(project_id=project_id)
    return APIResponse.success(data=data)
