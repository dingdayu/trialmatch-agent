from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.services.project_service import ProjectService
from app.services.audit_service import record_audit
from app.schemas.enums import ActionType, TargetType
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    phase: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目列表"""
    service = ProjectService(db)
    items, total = await service.list_projects(
        page=page, page_size=page_size,
        keyword=keyword, status=status, phase=phase,
    )
    return APIResponse.success(
        data={
            "items": [ProjectResponse.model_validate(p) for p in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("")
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """创建新项目"""
    service = ProjectService(db)
    try:
        project = await service.create_project(body.model_dump(), current_user.id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.CREATE,
            target_type=TargetType.PROJECT,
            target_id=project.id,
            project_id=project.id,
            after_value={"project_no": project.project_no},
        )
        return APIResponse.success(
            data={"id": project.id, "project_no": project.project_no}
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目详情"""
    service = ProjectService(db)
    try:
        project = await service.get_project(project_id)
        return APIResponse.success(data=ProjectResponse.model_validate(project))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """更新项目"""
    service = ProjectService(db)
    try:
        changes = body.model_dump(exclude_none=True)
        existing = await service.get_project(project_id)
        before = {key: getattr(existing, key, None) for key in changes}
        await service.update_project(project_id, changes)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.UPDATE,
            target_type=TargetType.PROJECT,
            target_id=project_id,
            project_id=project_id,
            before_value=before,
            after_value=changes,
        )
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "project_manager")),
):
    """删除项目"""
    service = ProjectService(db)
    try:
        existing = await service.get_project(project_id)
        before = {"project_no": existing.project_no, "study_name": existing.study_name}
        await service.delete_project(project_id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.DELETE,
            target_type=TargetType.PROJECT,
            target_id=project_id,
            project_id=project_id,
            before_value=before,
        )
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
