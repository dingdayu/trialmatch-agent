from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectListResponse
from app.services.subject_service import SubjectService
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
        await service.update_subject(subject_id, body.model_dump(exclude_none=True))
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
        await service.delete_subject(subject_id)
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
