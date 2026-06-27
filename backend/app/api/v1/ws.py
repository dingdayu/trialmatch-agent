"""WebSocket 接口 — 对应 Task 18.1, 接口 #51"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.dependencies import get_current_user_ws
from app.services.ws_manager import ws_manager
from app.utils.logger import logger

router = APIRouter()


@router.websocket("/projects/{project_id}/ws/screening/{run_id}")
async def screening_progress(
    websocket: WebSocket,
    project_id: str,
    run_id: str,
    token: str = Query(...),
):
    """#51 WebSocket: 初筛进度推送"""
    # 验证 token
    try:
        user = await get_current_user_ws(token)
    except Exception as e:
        await websocket.close(code=4001, reason="认证失败")
        return

    await ws_manager.connect(project_id, websocket)
    logger.info(f"用户 {user.username} 订阅初筛进度: run={run_id}")

    try:
        while True:
            # 保持连接，接收客户端心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(project_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket 异常: {str(e)}")
        await ws_manager.disconnect(project_id, websocket)
