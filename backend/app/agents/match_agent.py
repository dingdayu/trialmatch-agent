from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.agents.base import build_agent
from app.utils.logger import logger


class MatchCitation(BaseModel):
    quoted_text: str = Field(default="", description="引用的资料原文片段")
    extracted_fact: str = Field(default="", description="从原文提取的关键事实")
    relevance_explanation: str = Field(default="", description="该证据为何支持判断")


class MatchResult(BaseModel):
    result: str = Field(
        description="入选: pass/fail/insufficient_data/manual_review；排除: exclusion_hit/exclusion_not_hit/insufficient_data/manual_review"
    )
    confidence: int = Field(default=50, ge=0, le=100)
    rationale: str = Field(default="", description="判断理由与推理过程")
    citations: List[MatchCitation] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)


_SYSTEM = """你是一位专业的临床试验受试者筛选专家。根据临床入排标准，仔细分析受试者医疗资料，逐条判断是否符合。

规则：
1. 结论必须基于受试者资料中的客观证据，不得凭空推断。
2. 每条判断必须引用具体原文作为证据。
3. 资料不足以判断时，标注为 insufficient_data 或 manual_review。
4. 入选标准: pass(满足)/fail(不满足)/insufficient_data/manual_review。
5. 排除标准: exclusion_hit(命中排除)/exclusion_not_hit(未命中)/insufficient_data/manual_review。
6. 置信度: 有直接明确证据 >=85；间接证据 60-84；资料不足 <60。"""


class CriterionMatchAgent:
    """单条入排标准 → AI 匹配判断"""

    def __init__(self):
        self._agent = build_agent(
            instructions=_SYSTEM,
            output_schema=MatchResult,
            use_vision=False,
        )

    async def evaluate(
        self,
        criterion: dict,
        subject_info: dict,
        chunks_text: str,
        ai_prompt: Optional[str] = None,
    ) -> MatchResult:
        criterion_type_label = (
            "入选标准" if criterion.get("criterion_type") == "inclusion" else "排除标准"
        )

        prompt = f"""## 项目背景
{ai_prompt or "无特殊说明"}

## 受试者信息
- 编号: {subject_info.get("subject_no", "")}
- 性别: {subject_info.get("gender", "")}
- 年龄: {subject_info.get("age", "")}
- 诊断: {subject_info.get("diagnosis", "")}
- 研究中心: {subject_info.get("site_name", "")}

## 受试者医疗资料
{chunks_text[:8000]}

## {criterion_type_label}
- 标准编号: {criterion.get("criterion_code", "")}
- 标准内容: {criterion.get("criterion_text", "")}
- 标准说明: {criterion.get("criterion_explanation", "") or "无"}
- AI 辅助指令: {criterion.get("ai_instruction", "") or "无"}

请判断该受试者是否满足此{criterion_type_label}，给出结论、置信度、判断理由与原文引用。"""

        try:
            response = await self._agent.arun(prompt)
            result = response.content
            if isinstance(result, MatchResult):
                return result
            logger.warning(f"标准 {criterion.get('criterion_code')} 返回非结构化结果")
        except Exception as e:
            logger.warning(f"标准 {criterion.get('criterion_code')} 评估失败: {str(e)}")

        return MatchResult(result="insufficient_data", confidence=0, rationale="AI 评估异常或资料不足")
