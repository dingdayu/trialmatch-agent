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
        """解析 PDF 文件"""
        from app.utils.pdf_parser import PDFParser

        pages = PDFParser.parse(file_path)
        chunks = []
        for page in pages:
            if page.is_scanned:
                # 扫描件走 OCR
                try:
                    from app.utils.ocr_parser import OCRParser
                    text = OCRParser.recognize_image(page._image_bytes)
                except RuntimeError:
                    text = f"[扫描件 OCR 不可用，第 {page.page_no} 页]"
            else:
                text = page.text

            chunks.append({
                "page_no": page.page_no,
                "chunk_index": 0,
                "content": text,
                "bbox": None,
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
        """解析图片文件"""
        try:
            from app.utils.ocr_parser import OCRParser
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            text = OCRParser.recognize_image(image_bytes)
        except RuntimeError:
            text = "[图片 OCR 不可用]"

        return [{
            "page_no": 1,
            "chunk_index": 0,
            "content": text,
            "bbox": None,
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
                extracted_entities=None,
            )
            self.db.add(chunk)

        await self.db.flush()

    async def extract_entities(self, file_id: str) -> int:
        """对已解析的 chunks 调用 LLM 进行实体抽取"""
        from app.models.document_chunk import DocumentChunk

        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.file_id == file_id)
            .order_by(DocumentChunk.page_no, DocumentChunk.chunk_index)
        )
        chunks = list(result.scalars().all())

        if not chunks:
            return 0

        updated = 0
        for chunk in chunks:
            try:
                entities = await self._call_llm_entity_extraction(chunk.content)
                chunk.extracted_entities = entities
                updated += 1
            except Exception as e:
                logger.warning(f"实体抽取失败 chunk={chunk.id}: {str(e)}")

        await self.db.commit()
        return updated

    async def _call_llm_entity_extraction(self, text: str) -> dict:
        """调用 LLM 从文本中抽取结构化实体"""
        try:
            from app.services.ai_engine import LLMClient
            llm = LLMClient()

            prompt = f"""从以下医疗文本中提取结构化信息，仅输出 JSON：

{{
    "age": "年龄（数字）或 null",
    "birth_date": "出生日期或 null",
    "gender": "男/女 或 null",
    "diagnosis": "主要诊断或 null",
    "pathology": "病理类型或 null",
    "ecog_score": "ECOG 评分或 null",
    "lab_results": ["异常实验室检查结果列表"],
    "treatments": ["既往治疗方案列表"],
    "infections": ["感染病史列表"],
    "autoimmune_diseases": ["自身免疫疾病列表"]
}}

文本内容：
{text[:3000]}
"""
            result = await llm.chat(prompt)
            import json
            return json.loads(result) if isinstance(result, str) else result
        except Exception:
            return {}
