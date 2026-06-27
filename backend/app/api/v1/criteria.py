from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.criteria import CriteriaCreate, CriteriaUpdate, CriteriaResponse, CriteriaBatchImport
from app.services.criteria_service import CriteriaService
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}/criteria")
async def list_criteria(
    project_id: str,
    criterion_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目入排标准列表"""
    service = CriteriaService(db)
    items = await service.list_criteria(
        project_id=project_id,
        criterion_type=criterion_type,
        is_active=is_active,
    )
    return APIResponse.success(
        data=[CriteriaResponse.model_validate(c) for c in items]
    )


@router.post("/projects/{project_id}/criteria")
async def create_criterion(
    project_id: str,
    body: CriteriaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """新增入排标准"""
    service = CriteriaService(db)
    try:
        criterion = await service.create_criterion(project_id, body.model_dump())
        return APIResponse.success(data={"id": criterion.id})
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/criteria/{criterion_id}")
async def get_criterion(
    criterion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单条入排标准"""
    service = CriteriaService(db)
    try:
        criterion = await service.get_criterion(criterion_id)
        return APIResponse.success(data=CriteriaResponse.model_validate(criterion))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/criteria/{criterion_id}")
async def update_criterion(
    criterion_id: str,
    body: CriteriaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """更新入排标准"""
    service = CriteriaService(db)
    try:
        await service.update_criterion(criterion_id, body.model_dump(exclude_none=True))
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/criteria/{criterion_id}")
async def delete_criterion(
    criterion_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """删除入排标准"""
    service = CriteriaService(db)
    try:
        await service.delete_criterion(criterion_id)
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/criteria/batch-import")
async def batch_import_criteria(
    project_id: str,
    body: CriteriaBatchImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """批量导入入排标准"""
    service = CriteriaService(db)
    result = await service.batch_import(
        project_id, [c.model_dump() for c in body.criteria]
    )
    return APIResponse.success(data=result)
