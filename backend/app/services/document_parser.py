"""文档解析服务 — 对应 Task 9.5, 9.6
统一分片策略 + LLM 实体抽取"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.file import UploadedFile
from app.models.document_chunk import DocumentChunk
from app.utils.logger import logger

settings = get_settings()


class DocumentParserService:
    """文档解析服务：分片写入 + LLM 实体抽取"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def parse_file(self, file_id: str, force: bool = False) -> int:
        """解析文件：提取文本 → 分片 → 写入数据库 → 触发实体抽取"""
        result = await self.db.execute(
            select(UploadedFile).where(UploadedFile.id == file_id)
        )
        file_record = result.scalar_one_or_none()
        if not file_record:
            raise ValueError(f"文件 {file_id} 不存在")

        if file_record.parse_status == "completed" and not force:
            raise ValueError("文件已解析完成，如需重新解析请设置 force=true")

        # 更新状态为 processing
        file_record.parse_status = "processing"
        await self.db.commit()

        try:
            chunks = await self._extract_chunks(file_record)
            await self._save_chunks(file_record, chunks)
            file_record.parse_status = "completed"
            file_record.page_count = max((c.get("page_no", 1) for c in chunks), default=0)
            await self.db.commit()
            logger.info(f"文件 {file_id} 解析完成，共 {len(chunks)} 个片段")
            return len(chunks)
        except Exception as e:
            file_record.parse_status = "failed"
            await self.db.commit()
            logger.error(f"文件 {file_id} 解析失败: {str(e)}")
            raise

    async def _extract_chunks(self, file_record: UploadedFile) -> List[dict]:
        """根据文件类型选择解析器提取文本片段"""
        file_path = file_record.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_record.file_name or "")[1].lower()

        if ext == ".pdf":
            return await self._parse_pdf(file_path)
        elif ext in (".doc", ".docx"):
            return await self._parse_docx(file_path)
        elif ext in (".jpg", ".jpeg", ".png"):
            return await self._parse_image(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    async def _parse_pdf(self, file_path: str) -> List[dict]:
        """解析 PDF：文字页直接提取，扫描页走多模态视觉解析"""
        from app.utils.pdf_parser import PDFParser
        from app.agents import CaseParsingAgent

        pages = PDFParser.parse(file_path)
        agent = CaseParsingAgent()
        chunks = []
        for page in pages:
            if page.is_scanned:
                image_bytes = getattr(page, "_image_bytes", None)
                if image_bytes:
                    result = await agent.parse_image(image_bytes)
                    text = result.content
                    entities = result.entities.model_dump()
                else:
                    text = f"[第 {page.page_no} 页无法提取内容]"
                    entities = None
            else:
                text = page.text
                entities = None

            chunks.append({
                "page_no": page.page_no,
                "chunk_index": 0,
                "content": text,
                "bbox": None,
                "extracted_entities": entities,
            })
        return chunks

    async def _parse_docx(self, file_path: str) -> List[dict]:
        """解析 DOCX 文件"""
        from app.utils.docx_parser import DOCXParser

        docx_chunks = DOCXParser.parse(file_path)
        return [
            {
                "page_no": 1,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "bbox": None,
            }
            for c in docx_chunks
        ]

    async def _parse_image(self, file_path: str) -> List[dict]:
        """解析图片文件：多模态视觉模型转写 + 实体抽取"""
        from app.agents import CaseParsingAgent

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        result = await CaseParsingAgent().parse_image(image_bytes)

        return [{
            "page_no": 1,
            "chunk_index": 0,
            "content": result.content,
            "bbox": None,
            "extracted_entities": result.entities.model_dump(),
        }]

    async def _save_chunks(self, file_record: UploadedFile, chunks: List[dict]):
        """将分片写入 document_chunks 表（先删旧数据，再写新数据）"""
        # 删除旧分片
        from sqlalchemy import delete
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.file_id == file_record.id)
        )

        # 写入新分片
        for c in chunks:
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                file_id=file_record.id,
                project_id=file_record.project_id,
                subject_id=file_record.subject_id,
                page_no=c["page_no"],
                chunk_index=c["chunk_index"],
                content=c["content"],
                bbox=c.get("bbox"),
                extracted_entities=c.get("extracted_entities"),
            )
            self.db.add(chunk)

        await self.db.flush()

    async def extract_entities(self, file_id: str) -> int:
        """对尚未抽取实体的文本 chunk 调用多模态 Agent 补充结构化实体"""
        from app.models.document_chunk import DocumentChunk
        from app.agents import CaseParsingAgent

        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.file_id == file_id)
            .order_by(DocumentChunk.page_no, DocumentChunk.chunk_index)
        )
        chunks = list(result.scalars().all())

        if not chunks:
            return 0

        agent = CaseParsingAgent()
        updated = 0
        for chunk in chunks:
            if chunk.extracted_entities:
                continue
            if not chunk.content or not chunk.content.strip():
                continue
            try:
                parsed = await agent.parse_text(chunk.content)
                chunk.extracted_entities = parsed.entities.model_dump()
                updated += 1
            except Exception as e:
                logger.warning(f"实体抽取失败 chunk={chunk.id}: {str(e)}")

        await self.db.commit()
        return updated
