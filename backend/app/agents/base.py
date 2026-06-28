from __future__ import annotations

from typing import Optional, Type

from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


def _build_model(model_id: str, max_tokens: Optional[int] = None):
    from agno.models.openai.like import OpenAILike

    kwargs: dict = {
        "id": model_id,
        "api_key": settings.llm_api_key or None,
        "base_url": settings.llm_base_url,
        "temperature": settings.llm_temperature,
        "max_tokens": max_tokens or settings.llm_max_tokens,
        "timeout": settings.llm_timeout,
        "retries": settings.llm_max_retries,
        "delay_between_retries": settings.llm_retry_delay,
        "exponential_backoff": settings.llm_exponential_backoff,
    }
    if settings.llm_reasoning_effort:
        kwargs["reasoning_effort"] = settings.llm_reasoning_effort

    return OpenAILike(**kwargs)


def build_agent(
    instructions: str,
    output_schema: Optional[Type[BaseModel]] = None,
    use_vision: bool = False,
    max_tokens: Optional[int] = None,
):
    """构建 agno Agent，复用项目 LLM 配置。

    use_vision=True 时使用多模态视觉模型，可接收图片/文件输入。
    max_tokens 用于覆盖默认输出上限（如方案解析需更大上限避免 JSON 截断）。
    """
    from agno.agent import Agent

    model_id = settings.llm_vision_model_name if use_vision else settings.llm_model_name

    return Agent(
        model=_build_model(model_id, max_tokens=max_tokens),
        instructions=instructions,
        output_schema=output_schema,
        markdown=False,
    )
