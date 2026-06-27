"""导出模块 API — 对应 Task 15.3-15.5, 接口 #45-#47"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.services.export_service import ExportService
from app.utils.response import APIResponse
from app.models.user import User
from app.config import get_settings

settings = get_settings()
router = APIRouter()


@router.post("/subjects/{subject_id}/export-report")
async def create_export(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager", "crc")),
):
    """#45 创建导出任务"""
    service = ExportService(db)
    try:
        task = await service.create_export_task(subject_id, format="json")
        # 同步生成报告
        file_path = await service.generate_report(subject_id, task["export_task_id"])
        task["status"] = "completed"
        task["download_url"] = f"/api/v1/export-tasks/{task['export_task_id']}/download"
        return APIResponse.success(data=task, message="报告已生成")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/export-tasks/{task_id}")
async def get_export_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#46 获取导出任务状态"""
    service = ExportService(db)
    status = await service.get_export_status(task_id)
    return APIResponse.success(data=status)


@router.get("/export-tasks/{task_id}/download")
async def download_export(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#47 下载导出文件"""
    export_dir = os.path.join(settings.upload_dir, "exports")
    file_path = os.path.join(export_dir, f"{task_id}.json")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="导出文件不存在")

    return FileResponse(
        path=file_path,
        filename=f"report_{task_id}.json",
        media_type="application/json",
    )
