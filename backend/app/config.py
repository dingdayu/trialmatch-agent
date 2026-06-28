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

    # LLM 配置
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model_name: str = "gpt-4o-mini"
    # 多模态视觉模型：用于解析病例/检查报告图片与扫描件、研究方案
    # 需为支持图像/文件输入的模型（如 gpt-4o、qwen-vl-max 等）
    llm_vision_model_name: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    # 方案解析专用上限：入排标准是多条结构化列表，输出 token 远大于单条匹配，
    # 上限过小会导致 JSON 被截断、漏掉后半部分（如排除标准）
    llm_parse_max_tokens: int = 16384
    llm_timeout: int = 110
    llm_max_retries: int = 3
    # 重试间隔（秒）与指数退避：应对网关 524/限流（Cloudflare 建议 retry_after≈120）
    llm_retry_delay: int = 5
    llm_exponential_backoff: bool = True
    # 推理强度：gpt-5 系列推理模型用 low 可显著降低延迟，避免网关 120s 超时
    # 取值 minimal / low / medium / high；留空则用模型默认
    llm_reasoning_effort: str = "low"
    # 解析后是否自动触发受试者初筛匹配
    auto_screening_after_parse: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
