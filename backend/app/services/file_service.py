from __future__ import annotations

import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import UploadFile

from app.config import get_settings
from app.models.file import UploadedFile as UploadedFileModel
from app.models.subject import Subject

settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024  # 字节


class FileService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_project_file(
        self,
        project_id: str,
        file: UploadFile,
        file_type: str,
        user_id: str,
        description: Optional[str] = None,
    ) -> UploadedFileModel:
        """上传项目方案文件"""
        return await self._upload(
            project_id=project_id,
            subject_id=None,
            file=file,
            file_type=file_type,
            file_scope="project_protocol",
            user_id=user_id,
            description=description,
        )

    async def upload_subject_file(
        self,
        subject_id: str,
        file: UploadFile,
        file_type: str,
        user_id: str,
        description: Optional[str] = None,
    ) -> UploadedFileModel:
        """上传受试者资料文件"""
        subject = await self.db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = subject.scalar_one_or_none()
        if not subject:
            raise ValueError(f"受试者 {subject_id} 不存在")

        return await self._upload(
            project_id=subject.project_id,
            subject_id=subject_id,
            file=file,
            file_type=file_type,
            file_scope="subject_data",
            user_id=user_id,
            description=description,
        )

    async def _upload(
        self,
        project_id: str,
        subject_id: Optional[str],
        file: UploadFile,
        file_type: str,
        file_scope: str,
        user_id: str,
        description: Optional[str] = None,
    ) -> UploadedFileModel:
        """通用文件上传逻辑"""
        # 校验扩展名
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}，仅支持 PDF/JPG/PNG/DOC/DOCX")

        # 校验大小
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"文件大小超过限制 ({settings.max_upload_size_mb}MB)")

        # 生成存储路径
        upload_dir = os.path.join(
            settings.upload_dir,
            "projects",
            project_id,
            "subjects",
            subject_id or "_protocol",
        )
        os.makedirs(upload_dir, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}_{file.filename}"
        save_path = os.path.join(upload_dir, unique_name)

        # 写入磁盘
        with open(save_path, "wb") as f:
            f.write(content)

        # 推断 MIME 类型
        mime_type, _ = mimetypes.guess_type(file.filename)

        # 创建数据库记录
        file_record = UploadedFileModel(
            project_id=project_id,
            subject_id=subject_id,
            file_name=file.filename,
            file_path=save_path,
            file_type=file_type,
            file_scope=file_scope,
            mime_type=mime_type,
            file_size=len(content),
            parse_status="pending",
            description=description,
            uploaded_by=user_id,
            uploaded_at=datetime.utcnow(),
        )
        self.db.add(file_record)

        # 更新受试者素材计数
        if subject_id:
            subject_result = await self.db.execute(
                select(Subject).where(Subject.id == subject_id)
            )
            subject_obj = subject_result.scalar_one_or_none()
            if subject_obj:
                subject_obj.material_count = (subject_obj.material_count or 0) + 1

        await self.db.commit()
        await self.db.refresh(file_record)
        return file_record

    async def list_files(
        self,
        project_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        file_scope: Optional[str] = None,
        file_type: Optional[str] = None,
        parse_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[UploadedFileModel], int]:
        """获取文件列表"""
        query = select(UploadedFileModel)
        count_query = select(func.count()).select_from(UploadedFileModel)

        if project_id:
            query = query.where(UploadedFileModel.project_id == project_id)
            count_query = count_query.where(UploadedFileModel.project_id == project_id)
        if subject_id:
            query = query.where(UploadedFileModel.subject_id == subject_id)
            count_query = count_query.where(UploadedFileModel.subject_id == subject_id)
        if file_scope:
            query = query.where(UploadedFileModel.file_scope == file_scope)
            count_query = count_query.where(UploadedFileModel.file_scope == file_scope)
        if file_type:
            query = query.where(UploadedFileModel.file_type == file_type)
            count_query = count_query.where(UploadedFileModel.file_type == file_type)
        if parse_status:
            query = query.where(UploadedFileModel.parse_status == parse_status)
            count_query = count_query.where(UploadedFileModel.parse_status == parse_status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(UploadedFileModel.uploaded_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_file(self, file_id: str) -> UploadedFileModel:
        """获取文件详情"""
        result = await self.db.execute(
            select(UploadedFileModel).where(UploadedFileModel.id == file_id)
        )
        file_record = result.scalar_one_or_none()
        if not file_record:
            raise ValueError(f"文件 {file_id} 不存在")
        return file_record

    async def delete_file(self, file_id: str) -> None:
        """删除文件"""
        file_record = await self.get_file(file_id)
        # 删除磁盘文件
        if os.path.exists(file_record.file_path):
            os.remove(file_record.file_path)
        await self.db.delete(file_record)
        await self.db.commit()

    async def download_file(self, file_id: str) -> UploadedFileModel:
        """获取文件下载信息"""
        file_record = await self.get_file(file_id)
        if not os.path.exists(file_record.file_path):
            raise ValueError("文件已被删除")
        return file_record

    async def get_chunks(
        self,
        file_id: str,
        page_no: Optional[int] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ):
        """获取文件解析片段"""
        from app.models.document_chunk import DocumentChunk

        await self.get_file(file_id)  # 确保文件存在

        query = select(DocumentChunk).where(DocumentChunk.file_id == file_id)
        count_query = select(func.count()).select_from(DocumentChunk).where(DocumentChunk.file_id == file_id)

        if page_no is not None:
            query = query.where(DocumentChunk.page_no == page_no)
            count_query = count_query.where(DocumentChunk.page_no == page_no)
        if keyword:
            query = query.where(DocumentChunk.content.ilike(f"%{keyword}%"))
            count_query = count_query.where(DocumentChunk.content.ilike(f"%{keyword}%"))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(DocumentChunk.page_no, DocumentChunk.chunk_index).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
