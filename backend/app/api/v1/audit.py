"""审计日志 API — 对应 Task 17.2, 接口 #50"""

from __future__ import annotations

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.services.audit_service import AuditService
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("/audit-logs")
async def query_audit_logs(
    project_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """#50 查询审计日志（仅 admin）"""
    service = AuditService(db)

    start_dt = None
    end_dt = None
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
        except ValueError:
            pass
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
        except ValueError:
            pass

    items, total = await service.query_logs(
        project_id=project_id,
        subject_id=subject_id,
        user_id=user_id,
        action_type=action_type,
        target_type=target_type,
        start_time=start_dt,
        end_time=end_dt,
        page=page,
        page_size=page_size,
    )

    return APIResponse.success(
        data={
            "items": [
                {
                    "id": item.id,
                    "project_id": item.project_id,
                    "subject_id": item.subject_id,
                    "user_id": item.user_id,
                    "action_type": item.action_type,
                    "target_type": item.target_type,
                    "target_id": item.target_id,
                    "before_value": item.before_value,
                    "after_value": item.after_value,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )
