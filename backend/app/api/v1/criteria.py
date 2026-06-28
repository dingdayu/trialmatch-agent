from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.criteria import CriteriaCreate, CriteriaUpdate, CriteriaResponse, CriteriaBatchImport, CriteriaBatchUpdate
from app.services.criteria_service import CriteriaService
from app.services.audit_service import record_audit
from app.schemas.enums import ActionType, TargetType
from app.utils.response import APIResponse
from app.exceptions import NotFoundException, ConflictException
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
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.CREATE,
            target_type=TargetType.CRITERION,
            target_id=criterion.id,
            project_id=project_id,
            after_value={"criterion_code": criterion.criterion_code},
        )
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
        changes = body.model_dump(exclude_none=True)
        existing = await service.get_criterion(criterion_id)
        before = {key: getattr(existing, key, None) for key in changes}
        project_id = existing.project_id
        await service.update_criterion(criterion_id, changes)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.UPDATE,
            target_type=TargetType.CRITERION,
            target_id=criterion_id,
            project_id=project_id,
            before_value=before,
            after_value=changes,
        )
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
        existing = await service.get_criterion(criterion_id)
        before = {"criterion_code": existing.criterion_code, "criterion_type": existing.criterion_type}
        project_id = existing.project_id
        await service.delete_criterion(criterion_id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.DELETE,
            target_type=TargetType.CRITERION,
            target_id=criterion_id,
            project_id=project_id,
            before_value=before,
        )
        return APIResponse.success(data=True)
    except ValueError as e:
        raise NotFoundException(str(e))


@router.post("/projects/{project_id}/criteria/batch")
async def batch_update_criteria(
    project_id: str,
    body: CriteriaBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """批量操作入排标准 (reorder / toggle_active)"""
    service = CriteriaService(db)
    try:
        count = await service.batch_update(
            project_id=project_id,
            action=body.action,
            ids=body.ids,
            sort_orders=body.sort_orders,
            is_active=body.is_active,
        )
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.UPDATE,
            target_type=TargetType.CRITERION,
            project_id=project_id,
            after_value={"action": body.action, "ids": body.ids, "updated_count": count},
        )
        return APIResponse.success(data={"updated_count": count})
    except ValueError as e:
        raise NotFoundException(str(e))


@router.post("/projects/{project_id}/criteria/generate-from-protocol")
async def generate_criteria_from_protocol(
    project_id: str,
    file_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """从已上传的研究方案自动生成入排标准草稿（需人工确认）"""
    service = CriteriaService(db)
    try:
        result = await service.generate_from_protocol(project_id, file_id)
        return APIResponse.success(
            data={
                "generated_count": result["generated_count"],
                "criteria": [
                    CriteriaResponse.model_validate(c) for c in result["criteria"]
                ],
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
