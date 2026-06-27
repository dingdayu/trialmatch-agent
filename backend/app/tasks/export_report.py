"""导出报告 Celery 任务 — 对应 Task 15.2"""

from app.tasks.parse_document import run_export_report

__all__ = ["run_export_report"]
