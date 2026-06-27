"""WebSocket 连接管理 — 对应 Task 18.2"""

from __future__ import annotations

from typing import Dict, Set
import json

from fastapi import WebSocket
from app.utils.logger import logger


class WSManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # project_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        """接受 WebSocket 连接"""
        await websocket.accept()
        if project_id not in self._connections:
            self._connections[project_id] = set()
        self._connections[project_id].add(websocket)
        logger.info(f"WebSocket 已连接: project={project_id}, total={len(self._connections[project_id])}")

    async def disconnect(self, project_id: str, websocket: WebSocket):
        """断开 WebSocket 连接"""
        if project_id in self._connections:
            self._connections[project_id].discard(websocket)
            if not self._connections[project_id]:
                del self._connections[project_id]
        logger.info(f"WebSocket 已断开: project={project_id}")

    async def send_progress(self, project_id: str, run_id: str, progress: float, message: str = ""):
        """推送进度消息"""
        await self._broadcast(project_id, {
            "type": "progress",
            "run_id": run_id,
            "progress": progress,
            "message": message,
        })

    async def send_completed(self, project_id: str, run_id: str, result: dict):
        """推送分析完成消息"""
        await self._broadcast(project_id, {
            "type": "completed",
            "run_id": run_id,
            "result": result,
        })

    async def send_error(self, project_id: str, run_id: str, error: str):
        """推送分析失败消息"""
        await self._broadcast(project_id, {
            "type": "error",
            "run_id": run_id,
            "error": error,
        })

    async def send_file_progress(self, project_id: str, file_id: str, progress: float, message: str = ""):
        """推送文件解析进度消息"""
        await self._broadcast(project_id, {
            "type": "file_progress",
            "file_id": file_id,
            "progress": progress,
            "message": message,
        })

    async def _broadcast(self, project_id: str, data: dict):
        """向项目下所有连接广播消息"""
        if project_id not in self._connections:
            return

        message = json.dumps(data, ensure_ascii=False)
        disconnected = set()

        for ws in self._connections[project_id]:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        # 清理断开的连接
        for ws in disconnected:
            await self.disconnect(project_id, ws)


# 全局单例
ws_manager = WSManager()
