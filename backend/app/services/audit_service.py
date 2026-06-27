"""审计日志服务 — 对应 Task 17.1"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.audit_log import AuditLog


class AuditService:
    """审计日志服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        user_id: str,
        action_type: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        project_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        before_value: Optional[dict] = None,
        after_value: Optional[dict] = None,
    ) -> AuditLog:
        """记录审计日志"""
        entry = AuditLog(
            id=str(uuid.uuid4()),
            project_id=project_id,
            subject_id=subject_id,
            user_id=user_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            before_value=before_value,
            after_value=after_value,
        )
        self.db.add(entry)
        await self.db.commit()
        return entry

    async def query_logs(
        self,
        project_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[AuditLog], int]:
        """查询审计日志"""
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        if project_id:
            query = query.where(AuditLog.project_id == project_id)
            count_query = count_query.where(AuditLog.project_id == project_id)
        if subject_id:
            query = query.where(AuditLog.subject_id == subject_id)
            count_query = count_query.where(AuditLog.subject_id == subject_id)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action_type:
            query = query.where(AuditLog.action_type == action_type)
            count_query = count_query.where(AuditLog.action_type == action_type)
        if target_type:
            query = query.where(AuditLog.target_type == target_type)
            count_query = count_query.where(AuditLog.target_type == target_type)
        if start_time:
            query = query.where(AuditLog.created_at >= start_time)
            count_query = count_query.where(AuditLog.created_at >= start_time)
        if end_time:
            query = query.where(AuditLog.created_at <= end_time)
            count_query = count_query.where(AuditLog.created_at <= end_time)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
