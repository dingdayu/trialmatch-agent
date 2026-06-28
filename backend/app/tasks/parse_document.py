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


async def run_parse_and_screen(file_id: str, force: bool = False):
    """上传后台编排：解析文件 → 抽取实体 →（受试者文件且全部解析完成时）自动触发初筛"""
    from app.config import get_settings
    from app.database import async_session
    from app.models.file import UploadedFile
    from app.services.document_parser import DocumentParserService
    from sqlalchemy import select, func

    settings = get_settings()

    async with async_session() as db:
        file_result = await db.execute(
            select(UploadedFile).where(UploadedFile.id == file_id)
        )
        file_record = file_result.scalar_one_or_none()
        if not file_record:
            logger.warning(f"待解析文件不存在: {file_id}")
            return

        subject_id = file_record.subject_id
        file_scope = file_record.file_scope

        parser = DocumentParserService(db)
        try:
            await parser.parse_file(file_id, force=force)
            await parser.extract_entities(file_id)
        except Exception as e:
            logger.error(f"后台解析失败: file={file_id}, error={str(e)}")
            return

    if file_scope != "subject_data" or not subject_id:
        return
    if not settings.auto_screening_after_parse:
        return

    async with async_session() as db:
        pending = await db.execute(
            select(func.count()).select_from(UploadedFile).where(
                UploadedFile.subject_id == subject_id,
                UploadedFile.parse_status != "completed",
            )
        )
        if (pending.scalar() or 0) > 0:
            return

    await _auto_screen_subject(subject_id)


async def _auto_screen_subject(subject_id: str):
    """受试者文件全部解析完成后自动启动并执行一次初筛"""
    from app.database import async_session
    from app.models.subject import Subject
    from app.models.screening_run import ScreeningRun
    from app.services.screening_service import ScreeningService
    from sqlalchemy import select

    async with async_session() as db:
        subject_result = await db.execute(select(Subject).where(Subject.id == subject_id))
        subject = subject_result.scalar_one_or_none()
        if not subject:
            return

        running = await db.execute(
            select(ScreeningRun).where(
                ScreeningRun.subject_id == subject_id,
                ScreeningRun.status.in_(["queued", "running"]),
            )
        )
        if running.scalar_one_or_none():
            return

        service = ScreeningService(db)
        try:
            run = await service.start_screening(
                subject_id=subject_id,
                user_id=subject.created_by or "system",
            )
        except ValueError as e:
            logger.info(f"自动初筛跳过: subject={subject_id}, reason={str(e)}")
            return

    await run_single_screening(run.id)


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
