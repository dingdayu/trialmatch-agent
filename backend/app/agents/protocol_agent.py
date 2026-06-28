from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.agents.base import build_agent
from app.utils.logger import logger


class GeneratedCriterion(BaseModel):
    criterion_code: str = Field(description="标准编号，入选用 I-01/I-02，排除用 E-01/E-02")
    criterion_type: str = Field(description="inclusion 或 exclusion")
    criterion_text: str = Field(description="标准原文内容")
    criterion_explanation: str = Field(default="", description="对标准的解释说明")
    ai_instruction: str = Field(default="", description="供 AI 判断该标准时的要点指引")
    required_fields: List[str] = Field(default_factory=list, description="判断该标准所需的关键字段")


class ProtocolParseResult(BaseModel):
    criteria: List[GeneratedCriterion] = Field(default_factory=list)


_INSTRUCTIONS = """你是临床研究方案分析专家。你将收到一份临床试验研究方案（可能是 PDF、Word 或图片）。

任务：从方案中识别并抽取【全部】「入选标准」（inclusion）与【全部】「排除标准」（exclusion），输出结构化列表。

【至关重要 - 必须完整】方案通常包含两个独立小节：先是「入选标准」，紧接着是「排除标准」。
你必须把两个小节**逐条全部**抽取，绝不能只抽取入选标准就停止。
- 入选标准小节下的每一条（1、2、3 …）都要抽取为一条 inclusion。
- 排除标准小节下的每一条（1、2、3 …）都要抽取为一条 exclusion。
- 完成后请自检：原文「排除标准」小节有多少条编号，你的输出就应有多少条 exclusion，数量必须一致。

要求：
1. 入选标准编号使用 I-01、I-02 ...；排除标准编号使用 E-01、E-02 ...，各自从 01 开始，按方案中出现顺序编号。
2. criterion_text 保留方案原文表述，不要改写含义，不要合并多条为一条，也不要遗漏任何一条。
3. criterion_explanation 用一句话解释该标准的判断含义。
4. ai_instruction 给出从受试者病例中判断该标准时应关注的要点（例如需要哪些检查值、如何计算）。
5. required_fields 列出判断所需的关键字段（如 age、ecog_score、diagnosis、lab:中性粒细胞计数 等）。
6. 只抽取真实存在的标准，不要臆造。若某一类标准在方案中确实不存在，该类返回空即可。"""


class ProtocolParsingAgent:
    """研究方案 → 入排标准结构化抽取（多模态）"""

    def __init__(self):
        from app.config import get_settings

        self._agent = build_agent(
            instructions=_INSTRUCTIONS,
            output_schema=ProtocolParseResult,
            use_vision=True,
            max_tokens=get_settings().llm_parse_max_tokens,
        )

    async def parse(
        self,
        text_content: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        file_ext: Optional[str] = None,
    ) -> List[GeneratedCriterion]:
        from app.agents.media_loader import load_document_payload

        text = text_content
        image_bytes_list: List[bytes] = []

        if text is None and file_bytes and file_ext:
            text, image_bytes_list = load_document_payload(file_bytes, file_ext)
            logger.info(
                f"[入排解析] 文档加载完成: ext={file_ext}, "
                f"文本字符数={len(text or '')}, 图片页数={len(image_bytes_list)}"
            )

        if not text and not image_bytes_list:
            logger.warning("[入排解析] 研究方案无可解析内容，跳过 LLM 调用")
            return []

        inclusion = await self._extract_type("inclusion", "入选标准", "I", text, image_bytes_list)
        exclusion = await self._extract_type("exclusion", "排除标准", "E", text, image_bytes_list)

        criteria = inclusion + exclusion
        logger.info(
            f"[入排解析] 解析完成: 共 {len(criteria)} 条 "
            f"({len(inclusion)} 入选 / {len(exclusion)} 排除)"
        )
        return criteria

    async def _extract_type(
        self,
        ctype: str,
        type_label: str,
        code_prefix: str,
        text: Optional[str],
        image_bytes_list: List[bytes],
    ) -> List[GeneratedCriterion]:
        """单独抽取某一类标准（入选/排除），分两次调用避免漏抽长列表"""
        import time

        from agno.media import Image

        prompt = (
            f"请只抽取这份研究方案中【{type_label}】小节下的【全部】条目，逐条不漏。"
            f"忽略另一类标准。每一条编号（1、2、3 …）都必须输出为一条 {ctype}。"
        )
        if text:
            prompt = f"{prompt}\n\n方案文本内容：\n{text}"

        images = [Image(content=b) for b in image_bytes_list] or None

        model_id = getattr(self._agent.model, "id", "unknown") if self._agent.model else "unknown"
        logger.info(
            f"[入排解析] 抽取「{type_label}」开始: model={model_id}, prompt长度={len(prompt)}"
        )

        started = time.monotonic()
        try:
            response = await self._agent.arun(prompt, images=images)
        except Exception as e:
            logger.error(f"[入排解析] 「{type_label}」LLM 调用异常: {type(e).__name__}: {str(e)}")
            raise

        elapsed_ms = round((time.monotonic() - started) * 1000)
        result = response.content
        raw_preview = self._stringify_response(result)
        logger.info(
            f"[入排解析] 「{type_label}」响应: 耗时={elapsed_ms}ms, 类型={type(result).__name__}"
        )
        logger.info(f"[入排解析] 「{type_label}」原始响应（前 3000 字）:\n{raw_preview[:3000]}")

        if not isinstance(result, ProtocolParseResult):
            logger.warning(f"[入排解析] 「{type_label}」返回非结构化结果，已忽略")
            return []

        items = [c for c in result.criteria if c.criterion_type == ctype]
        for idx, c in enumerate(items, start=1):
            c.criterion_code = f"{code_prefix}-{idx:02d}"
            c.criterion_type = ctype
            logger.info(f"[入排解析]   -> [{c.criterion_code}] {c.criterion_text[:60]}")
        logger.info(f"[入排解析] 「{type_label}」抽取到 {len(items)} 条")
        return items

    @staticmethod
    def _stringify_response(result: object) -> str:
        if isinstance(result, BaseModel):
            return result.model_dump_json(indent=2)
        return str(result)
