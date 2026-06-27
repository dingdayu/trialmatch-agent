"""文件相关 Schema"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


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


class ParseTriggerRequest(BaseModel):
    """触发文件解析请求"""
    force: bool = Field(default=False, description="是否强制重解析")


class ParseTriggerResponse(BaseModel):
    """触发文件解析响应"""
    file_id: str
    status: str = "queued"
    message: str = "解析任务已提交"


class ChunkResponse(BaseModel):
    """文件解析片段响应"""
    id: str
    file_id: str
    page_no: int
    chunk_index: int
    content: str
    bbox: Optional[dict] = None
    extracted_entities: Optional[dict] = None

    class Config:
        from_attributes = True


class ChunkListResponse(BaseModel):
    """片段列表响应"""
    items: list
    total: int
    page: int
    page_size: int
