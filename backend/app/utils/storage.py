"""本地文件存储工具 — 对应技术设计文档 Task 8.1"""

import os
import shutil
from pathlib import Path

from app.config import get_settings

settings = get_settings()


class LocalStorage:
    """本地文件存储封装"""

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or settings.upload_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save(self, relative_path: str, content: bytes) -> str:
        """保存文件到本地，返回完整路径"""
        full_path = os.path.join(self.base_dir, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(content)
        return full_path

    def read(self, file_path: str) -> bytes:
        """读取本地文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        with open(file_path, "rb") as f:
            return f.read()

    def delete(self, file_path: str) -> None:
        """删除本地文件"""
        if os.path.exists(file_path):
            os.remove(file_path)
            # 尝试清理空目录
            parent = os.path.dirname(file_path)
            if not os.listdir(parent):
                os.rmdir(parent)

    def get_project_dir(self, project_id: str) -> str:
        """获取项目存储目录"""
        return os.path.join(self.base_dir, "projects", project_id)

    def get_subject_dir(self, project_id: str, subject_id: str) -> str:
        """获取受试者存储目录"""
        return os.path.join(self.base_dir, "projects", project_id, "subjects", subject_id)


# 全局单例
storage = LocalStorage()
