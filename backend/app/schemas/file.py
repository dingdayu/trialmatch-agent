from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class FileResponse(BaseModel):
    """文件信息响应"""
    id: str
    project_id: str
    subject_id: Optional[str] = None
    file_name: str
    file_type: str
    file_scope: str
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    page_count: Optional[int] = None
    parse_status: str
    description: Optional[str] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """文件列表响应"""
    items: List[FileResponse]
    total: int
    page: int
    page_size: int
