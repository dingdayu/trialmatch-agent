from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.file import FileResponse, FileListResponse, ParseTriggerRequest, ParseTriggerResponse, ChunkResponse
from app.services.file_service import FileService
from app.services.audit_service import record_audit
from app.schemas.enums import ActionType, TargetType
from app.tasks.parse_document import run_parse_and_screen
from app.utils.response import APIResponse
from app.utils.logger import logger
from app.exceptions import NotFoundException
from app.models.user import User

router = APIRouter()


def _schedule_parse(file_id: str, force: bool = False) -> None:
    """在事件循环中后台触发解析+实体抽取（+受试者文件自动初筛）"""
    async def _runner():
        try:
            await run_parse_and_screen(file_id, force=force)
        except Exception as e:
            logger.error(f"后台解析编排异常: file={file_id}, error={str(e)}")

    asyncio.create_task(_runner())


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
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.UPLOAD,
            target_type=TargetType.FILE,
            target_id=result.id,
            project_id=project_id,
            after_value={"file_name": result.file_name, "file_type": file_type, "file_scope": "project_protocol"},
        )
        if auto_parse:
            _schedule_parse(result.id)
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
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.UPLOAD,
            target_type=TargetType.FILE,
            target_id=result.id,
            project_id=result.project_id,
            subject_id=subject_id,
            after_value={"file_name": result.file_name, "file_type": file_type, "file_scope": "subject_data"},
        )
        if auto_parse:
            _schedule_parse(result.id)
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
        existing = await service.get_file(file_id)
        before = {"file_name": existing.file_name, "file_scope": existing.file_scope}
        project_id = existing.project_id
        subject_id = existing.subject_id
        await service.delete_file(file_id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.DELETE,
            target_type=TargetType.FILE,
            target_id=file_id,
            project_id=project_id,
            subject_id=subject_id,
            before_value=before,
        )
        return APIResponse.success(data=True)
    except ValueError as e:
        raise NotFoundException(str(e))


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """下载文件"""
    service = FileService(db)
    try:
        file_record = await service.download_file(file_id)
        await record_audit(
            db,
            user_id=current_user.id,
            action_type=ActionType.DOWNLOAD,
            target_type=TargetType.FILE,
            target_id=file_id,
            project_id=file_record.project_id,
            subject_id=file_record.subject_id,
            after_value={"file_name": file_record.file_name},
        )
        return FastAPIFileResponse(
            path=file_record.file_path,
            filename=file_record.file_name,
            media_type=file_record.mime_type or "application/octet-stream",
        )
    except ValueError as e:
        raise NotFoundException(str(e))


@router.post("/{file_id}/parse")
async def trigger_parse(
    file_id: str,
    body: ParseTriggerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """触发文件解析（后台异步执行，前端可轮询 parse_status）"""
    service = FileService(db)
    try:
        file_record = await service.get_file(file_id)
        file_record.parse_status = "pending"
        await db.commit()

        _schedule_parse(file_id, force=body.force)

        return APIResponse.success(
            data=ParseTriggerResponse(
                file_id=file_id,
                status="queued",
                message="解析任务已提交" if not body.force else "强制重解析任务已提交",
            ).model_dump()
        )
    except ValueError as e:
        raise NotFoundException(str(e))


@router.get("/{file_id}/chunks")
async def get_file_chunks(
    file_id: str,
    page_no: Optional[int] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文件解析片段"""
    service = FileService(db)
    try:
        items, total = await service.get_chunks(
            file_id=file_id,
            page_no=page_no,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
        return APIResponse.success(
            data={
                "items": [ChunkResponse.model_validate(c) for c in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )
    except ValueError as e:
        raise NotFoundException(str(e))
