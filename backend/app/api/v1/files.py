from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.file import FileResponse, FileListResponse
from app.services.file_service import FileService
from app.utils.response import APIResponse
from app.models.user import User

router = APIRouter()


@router.post("/projects/{project_id}/files")
async def upload_project_file(
    project_id: str,
    file: UploadFile = File(...),
    file_scope: str = Form(default="project_protocol"),
    file_type: str = Form(...),
    description: Optional[str] = Form(None),
    auto_parse: bool = Form(default=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传项目方案文件"""
    service = FileService(db)
    try:
        result = await service.upload_project_file(
            project_id=project_id,
            file=file,
            file_type=file_type,
            user_id=current_user.id,
            description=description,
        )
        return APIResponse.success(data=FileResponse.model_validate(result))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subjects/{subject_id}/files")
async def upload_subject_file(
    subject_id: str,
    file: UploadFile = File(...),
    file_scope: str = Form(default="subject_data"),
    file_type: str = Form(...),
    description: Optional[str] = Form(None),
    auto_parse: bool = Form(default=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传受试者资料文件"""
    service = FileService(db)
    try:
        result = await service.upload_subject_file(
            subject_id=subject_id,
            file=file,
            file_type=file_type,
            user_id=current_user.id,
            description=description,
        )
        return APIResponse.success(data=FileResponse.model_validate(result))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def list_files(
    project_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    file_scope: Optional[str] = None,
    file_type: Optional[str] = None,
    parse_status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件列表"""
    service = FileService(db)
    items, total = await service.list_files(
        project_id=project_id,
        subject_id=subject_id,
        file_scope=file_scope,
        file_type=file_type,
        parse_status=parse_status,
        page=page,
        page_size=page_size,
    )
    return APIResponse.success(
        data={
            "items": [FileResponse.model_validate(f) for f in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.get("/{file_id}")
async def get_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件详情"""
    service = FileService(db)
    try:
        result = await service.get_file(file_id)
        return APIResponse.success(data=FileResponse.model_validate(result))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文件"""
    service = FileService(db)
    try:
        await service.delete_file(file_id)
        return APIResponse.success(data=True)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
