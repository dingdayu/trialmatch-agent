"""文件数据访问层 — 对应 Task 8.3"""

from __future__ import annotations

from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.file import UploadedFile
from app.repositories.base_repo import BaseRepository


class FileRepository(BaseRepository):
    """文件数据访问层"""
    model = UploadedFile

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def list_with_filters(
        self,
        project_id: Optional[str] = None,
        subject_id: Optional[str] = None,
        file_scope: Optional[str] = None,
        file_type: Optional[str] = None,
        parse_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[UploadedFile], int]:
        query = select(UploadedFile)
        count_query = select(func.count()).select_from(UploadedFile)

        if project_id:
            query = query.where(UploadedFile.project_id == project_id)
            count_query = count_query.where(UploadedFile.project_id == project_id)
        if subject_id:
            query = query.where(UploadedFile.subject_id == subject_id)
            count_query = count_query.where(UploadedFile.subject_id == subject_id)
        if file_scope:
            query = query.where(UploadedFile.file_scope == file_scope)
            count_query = count_query.where(UploadedFile.file_scope == file_scope)
        if file_type:
            query = query.where(UploadedFile.file_type == file_type)
            count_query = count_query.where(UploadedFile.file_type == file_type)
        if parse_status:
            query = query.where(UploadedFile.parse_status == parse_status)
            count_query = count_query.where(UploadedFile.parse_status == parse_status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(UploadedFile.uploaded_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
