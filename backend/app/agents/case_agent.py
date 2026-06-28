from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.agents.base import build_agent
from app.utils.logger import logger


class LabResult(BaseModel):
    name: str
    value: str
    unit: str = ""


class ExtractedEntities(BaseModel):
    age: Optional[int] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    pathology: Optional[str] = None
    ecog_score: Optional[str] = None
    lab_results: List[LabResult] = Field(default_factory=list)
    treatments: List[str] = Field(default_factory=list)
    infections: List[str] = Field(default_factory=list)
    autoimmune_diseases: List[str] = Field(default_factory=list)


class CasePageResult(BaseModel):
    content: str = Field(description="该页/该图的完整文字内容（含表格、检查值，按阅读顺序）")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)


_INSTRUCTIONS = """你是临床病历多模态解析专家。你将收到受试者的病例、检查报告、化验单或影像报告（图片或文档页面）。

任务：
1. content：完整、准确地转写该页面中的全部文字内容，包括表格、检查指标、数值与单位，保持医学术语原文。
2. entities：从内容中抽取结构化关键实体（年龄、出生日期、性别、诊断、病理、ECOG 评分、异常实验室结果、既往治疗、感染史、自身免疫疾病）。

要求：
- 不得臆造任何未出现在资料中的信息，找不到的字段留空/null。
- 数值类指标必须保留单位。
- 若页面无可读内容，content 返回空字符串。"""


class CaseParsingAgent:
    """受试者病例/检查报告 → 多模态文字转写 + 实体抽取"""

    def __init__(self):
        self._agent = build_agent(
            instructions=_INSTRUCTIONS,
            output_schema=CasePageResult,
            use_vision=True,
        )

    async def parse_image(self, image_bytes: bytes) -> CasePageResult:
        from agno.media import Image

        return await self._run(
            "请转写并解析这张临床资料图片。",
            images=[Image(content=image_bytes)],
        )

    async def parse_file(self, file_bytes: bytes) -> CasePageResult:
        from agno.media import File

        return await self._run(
            "请转写并解析这份临床资料文档。",
            files=[File(content=file_bytes)],
        )

    async def parse_text(self, text: str) -> CasePageResult:
        return await self._run(
            f"请解析以下临床资料文本并抽取结构化实体：\n\n{text}",
        )

    async def _run(self, prompt: str, images=None, files=None) -> CasePageResult:
        try:
            response = await self._agent.arun(prompt, images=images, files=files)
            result = response.content
            if isinstance(result, CasePageResult):
                return result
            logger.warning("CaseParsingAgent 返回非结构化结果")
        except Exception as e:
            logger.warning(f"CaseParsingAgent 解析失败: {str(e)}")
        return CasePageResult(content="")
