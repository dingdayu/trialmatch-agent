from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectListResponse
from app.services.subject_service import SubjectService
from app.services.audit_service import record_audit
from app.schemas.enums import ActionType, TargetType
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}/subjects")
async def list_subjects(
    project_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    screening_status: Optional[str] = None,
    overall_result: Optional[str] = None,
    site_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目下受试者列表"""
    service = SubjectService(db)
    items, total = await service.list_subjects(
        project_id=project_id,
        page=page, page_size=page_size,
        keyword=keyword,
        screening_status=screening_status,
        overall_result=overall_result,
        site_name=site_name,
    )
    return APIResponse.success(
        data={
            "items": [SubjectResponse.model_validate(s) for s in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("/projects/{project_id}/subjects")
async def create_subject(
    project_id: str,
    body: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增受试者"""
    service = SubjectService(db)
    try:
        subject = await service.create_subject(project_id, body.model_dump(), current_user.id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.CREATE,
            target_type=TargetType.SUBJECT,
            target_id=subject.id,
            project_id=project_id,
            subject_id=subject.id,
            after_value={"subject_no": subject.subject_no},
        )
        return APIResponse.success(data={"id": subject.id, "subject_no": subject.subject_no})
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/subjects/{subject_id}")
async def get_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取受试者详情"""
    service = SubjectService(db)
    try:
        subject = await service.get_subject(subject_id)
        return APIResponse.success(data=SubjectResponse.model_validate(subject))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/subjects/{subject_id}")
async def update_subject(
    subject_id: str,
    body: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新受试者"""
    service = SubjectService(db)
    try:
        changes = body.model_dump(exclude_none=True)
        existing = await service.get_subject(subject_id)
        before = {key: getattr(existing, key, None) for key in changes}
        await service.update_subject(subject_id, changes)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.UPDATE,
            target_type=TargetType.SUBJECT,
            target_id=subject_id,
            project_id=existing.project_id,
            subject_id=subject_id,
            before_value=before,
            after_value=changes,
        )
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除受试者"""
    service = SubjectService(db)
    try:
        existing = await service.get_subject(subject_id)
        before = {"subject_no": existing.subject_no, "project_id": existing.project_id}
        project_id = existing.project_id
        await service.delete_subject(subject_id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.DELETE,
            target_type=TargetType.SUBJECT,
            target_id=subject_id,
            project_id=project_id,
            subject_id=subject_id,
            before_value=before,
        )
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
