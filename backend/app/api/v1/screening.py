"""AI 初筛模块 API — 对应 Task 12.6-12.11, 接口 #32-#37"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.screening import (
    ScreeningRunRequest,
    BatchRunRequest,
    ScreeningRunResponse,
    ScreeningRunListItem,
    ScreeningRunDetail,
    RerunRequest,
    BatchRunResponse,
)
from app.services.screening_service import ScreeningService
from app.utils.response import APIResponse
from app.models.user import User
from app.utils.logger import logger

router = APIRouter()


@router.post("/subjects/{subject_id}/screening-runs", response_model=APIResponse)
async def start_screening(
    subject_id: str,
    body: ScreeningRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager", "crc")),
):
    """#32 启动单个 AI 初筛"""
    service = ScreeningService(db)
    try:
        run = await service.start_screening(
            subject_id=subject_id,
            user_id=current_user.id,
            model_name=body.model_name,
            prompt_version=body.prompt_version,
            criteria_ids=body.criteria_ids,
            force_reparse=body.force_reparse_files,
        )
        logger.info(f"启动初筛: {run.run_no}", extra={"user_id": current_user.id})
        return APIResponse.success(
            data=ScreeningRunResponse.model_validate(run).model_dump(),
            message="初筛任务已创建",
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/subjects/{subject_id}/screening-runs/{run_id}/execute", response_model=APIResponse)
async def execute_screening(
    subject_id: str,
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager", "crc")),
):
    """执行 AI 初筛（同步）"""
    service = ScreeningService(db)
    try:
        result = await service.execute_screening(run_id)
        return APIResponse.success(data=result, message="初筛完成")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初筛执行失败: {str(e)}")


@router.post("/projects/{project_id}/screening/batch-run", response_model=APIResponse)
async def batch_start_screening(
    project_id: str,
    body: BatchRunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager", "crc")),
):
    """#33 批量启动 AI 初筛"""
    service = ScreeningService(db)
    try:
        result = await service.batch_start_screening(
            subject_ids=body.subject_ids,
            user_id=current_user.id,
            model_name=body.model_name,
            prompt_version=body.prompt_version,
            criteria_ids=body.criteria_ids,
            force_reparse=body.force_reparse_files,
        )
        return APIResponse.success(
            data=BatchRunResponse(
                batch_id=result["batch_id"],
                runs=[ScreeningRunResponse.model_validate(r) for r in result["runs"]],
                skipped_count=result["skipped_count"],
                skipped_reasons=result["skipped_reasons"],
            ).model_dump(),
            message=f"已创建 {len(result['runs'])} 个初筛任务",
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/subjects/{subject_id}/screening-runs", response_model=APIResponse)
async def list_screening_runs(
    subject_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#34 获取 AI 任务列表"""
    service = ScreeningService(db)
    items, total = await service.list_runs(subject_id, page=page, page_size=page_size)
    return APIResponse.success(
        data={
            "items": [ScreeningRunListItem.model_validate(r).model_dump() for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/screening-runs/{run_id}", response_model=APIResponse)
async def get_screening_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """#35 获取 AI 任务详情"""
    service = ScreeningService(db)
    try:
        run = await service.get_run_detail(run_id)
        data = ScreeningRunDetail.model_validate(run).model_dump()
        data["summary"] = getattr(run, "_summary", None)
        return APIResponse.success(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/screening-runs/{run_id}/rerun", response_model=APIResponse)
async def rerun_screening(
    run_id: str,
    body: RerunRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager", "crc")),
):
    """#36 重新运行 AI 初筛"""
    service = ScreeningService(db)
    try:
        run = await service.rerun_screening(
            run_id=run_id,
            user_id=current_user.id,
            model_name=body.model_name,
            prompt_version=body.prompt_version,
            criteria_ids=body.criteria_ids,
        )
        return APIResponse.success(
            data=ScreeningRunResponse.model_validate(run).model_dump(),
            message="重跑任务已创建",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/subjects/{subject_id}/confirm-all", response_model=APIResponse)
async def confirm_all(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager", "crc")),
):
    """#37 标记人工确认完成"""
    service = ScreeningService(db)
    try:
        count = await service.confirm_all(subject_id)
        return APIResponse.success(
            data={"confirmed_count": count, "subject_id": subject_id, "new_status": "completed"},
            message=f"已确认 {count} 条匹配结果",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
