"""Celery 实例配置 — 对应 Task 9.7, 12.4, 12.5, 15.2"""

# 由于当前环境使用 SQLite 且不依赖 Celery/Redis，
# 所有异步任务通过直接函数调用实现。
# 本文件保留 Celery 接口定义，供后续扩展。

from __future__ import annotations

import asyncio
from typing import Optional

from app.utils.logger import logger


async def run_parse_document(file_id: str, force: bool = False):
    """解析文档任务（异步版本）"""
    from app.database import async_session
    from app.services.document_parser import DocumentParserService

    async with async_session() as db:
        service = DocumentParserService(db)
        chunk_count = await service.parse_file(file_id, force=force)
        logger.info(f"文档解析完成: file={file_id}, chunks={chunk_count}")
        return chunk_count


async def run_single_screening(run_id: str):
    """执行单个 AI 初筛任务（异步版本）"""
    from app.database import async_session
    from app.services.screening_service import ScreeningService

    async with async_session() as db:
        service = ScreeningService(db)
        result = await service.execute_screening(run_id)
        logger.info(f"AI 初筛完成: run={run_id}")
        return result


async def run_batch_screening(subject_ids: list, user_id: str,
                              model_name: Optional[str] = None,
                              prompt_version: Optional[str] = None,
                              criteria_ids: Optional[list] = None,
                              force_reparse: bool = False):
    """批量执行 AI 初筛（异步版本）"""
    from app.database import async_session
    from app.services.screening_service import ScreeningService

    async with async_session() as db:
        service = ScreeningService(db)
        result = await service.batch_start_screening(
            subject_ids=subject_ids,
            user_id=user_id,
            model_name=model_name,
            prompt_version=prompt_version,
            criteria_ids=criteria_ids,
            force_reparse=force_reparse,
        )

        # 逐个执行
        for run in result["runs"]:
            try:
                await service.execute_screening(run.id)
            except Exception as e:
                logger.error(f"批量初筛: run={run.id} 失败: {str(e)}")

        return result


async def run_export_report(subject_id: str, task_id: str, format: str = "json"):
    """导出报告任务（异步版本）"""
    from app.database import async_session
    from app.services.export_service import ExportService

    async with async_session() as db:
        service = ExportService(db)
        file_path = await service.generate_report(subject_id, task_id, format=format)
        logger.info(f"报告导出完成: task={task_id}")
        return file_path
