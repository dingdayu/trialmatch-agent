"""
TrialMatch AI 配置管理模块

基于 pydantic-settings 管理所有环境变量
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ============================================
    # 应用基础配置
    # ============================================
    APP_NAME: str = "TrialMatch AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ============================================
    # 数据库配置 (SQLite3)
    # ============================================
    DATABASE_URL: str = "sqlite+aiosqlite:///./trialmatch.db"

    # ============================================
    # Redis 配置
    # ============================================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ============================================
    # 本地文件存储配置
    # ============================================
    RESOURCE_DIR: str = "./resources"

    # ============================================
    # LLM 配置
    # ============================================
    LLM_BASE_URL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 120
    LLM_MAX_RETRIES: int = 3

    # ============================================
    # JWT 配置
    # ============================================
    JWT_SECRET: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 7200  # 2 hours
    JWT_REFRESH_TOKEN_EXPIRE_SECONDS: int = 604800  # 7 days

    # ============================================
    # CORS 配置
    # ============================================
    CORS_ORIGINS: list[str] = ["*"]

    # ============================================
    # 文件上传配置
    # ============================================
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: list[str] = [
        "pdf", "doc", "docx", "jpg", "jpeg", "png"
    ]

    @property
    def resource_path(self) -> Path:
        """获取资源目录的绝对路径"""
        path = Path(self.RESOURCE_DIR)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path


# 全局配置实例
settings = Settings()
