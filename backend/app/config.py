from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置，自动从 .env 文件读取"""

    app_name: str = "TrialMatch AI"
    app_version: str = "0.1.0"
    debug: bool = True

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./resource/trialmatch.db"

    # JWT
    jwt_secret: str = "changeme"
    jwt_expire_seconds: int = 86400  # 24 小时

    # 文件上传
    upload_dir: str = "./resource/uploads"
    max_upload_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
