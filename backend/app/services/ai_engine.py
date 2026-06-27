"""LLM 客户端封装 — 对应 Task 10.1
使用 OpenAI 兼容接口"""

from __future__ import annotations

import json
from typing import Optional, List

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


class LLMClient:
    """LLM 客户端：OpenAI 兼容接口封装"""

    def __init__(self, model: Optional[str] = None):
        self.base_url = getattr(settings, "llm_base_url", "https://api.openai.com/v1")
        self.api_key = getattr(settings, "llm_api_key", "")
        self.model = model or getattr(settings, "llm_model_name", "gpt-4o-mini")
        self.temperature = getattr(settings, "llm_temperature", 0.1)
        self.max_tokens = getattr(settings, "llm_max_tokens", 4096)
        self.timeout = getattr(settings, "llm_timeout", 120)
        self.max_retries = getattr(settings, "llm_max_retries", 3)

    async def chat(self, prompt: str, system_prompt: str = "") -> str:
        """发送聊天请求，返回文本响应"""
        import httpx

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def chat_with_retry(self, prompt: str, system_prompt: str = "") -> str:
        """带重试的聊天请求（3 次重试 + 指数退避）"""
        import asyncio

        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await self.chat(prompt, system_prompt)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM 调用失败 (第 {attempt + 1}/{self.max_retries} 次): {str(e)}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"LLM 调用失败，已重试 {self.max_retries} 次: {str(last_error)}")

    async def chat_json(self, prompt: str, system_prompt: str = "") -> dict:
        """发送聊天请求，返回 JSON 解析结果"""
        response = await self.chat_with_retry(prompt, system_prompt)

        # 尝试提取 JSON（处理 LLM 可能添加的 markdown 包裹）
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            logger.error(f"LLM 返回非 JSON 格式: {response[:500]}")
            raise ValueError("LLM 返回格式异常，无法解析为 JSON")


class AIEngine:
    """AI 匹配引擎 — 对应 Task 10.3, 10.4, 10.5"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    async def evaluate_criterion(
        self,
        criterion: dict,
        subject_info: dict,
        chunks_text: str,
        ai_prompt: Optional[str] = None,
    ) -> dict:
        """对单条标准进行 LLM 匹配判断"""
        from app.utils.prompt_builder import PromptBuilder

        prompt = PromptBuilder.build_criterion_evaluation_prompt(
            criterion=criterion,
            subject_info=subject_info,
            chunks_text=chunks_text,
            ai_prompt=ai_prompt,
        )

        result = await self.llm.chat_json(prompt, system_prompt=PromptBuilder.SYSTEM_ROLE)

        return self._parse_criterion_result(result, criterion)

    def _parse_criterion_result(self, llm_result: dict, criterion: dict) -> dict:
        """解析 LLM 返回的标准匹配结果 — Task 10.3"""
        return {
            "criterion_id": criterion.get("id", ""),
            "criterion_code": criterion.get("criterion_code", ""),
            "criterion_type": criterion.get("criterion_type", ""),
            "criterion_text": criterion.get("criterion_text", ""),
            "ai_result": llm_result.get("result", "insufficient_data"),
            "confidence_score": llm_result.get("confidence", 50),
            "ai_rationale": llm_result.get("rationale", ""),
            "citations": llm_result.get("citations", []),
            "missing_info": llm_result.get("missing_info", []),
        }

    @staticmethod
    def compute_overall_result(evaluations: list) -> str:
        """按规则引擎计算总体结论 — Task 10.4"""
        if not evaluations:
            return "insufficient_data"

        inclusion_fail = 0
        inclusion_insufficient = 0
        exclusion_hit = 0
        exclusion_insufficient = 0
        has_pending = False

        for e in evaluations:
            ct = getattr(e, "criterion_type", "") if hasattr(e, "criterion_type") else e.get("criterion_type", "")
            ar = getattr(e, "ai_result", "") if hasattr(e, "ai_result") else e.get("ai_result", "")

            if ar == "manual_review":
                has_pending = True

            if ct == "inclusion":
                if ar == "fail":
                    inclusion_fail += 1
                elif ar in ("insufficient_data", "manual_review"):
                    inclusion_insufficient += 1
            elif ct == "exclusion":
                if ar == "exclusion_hit":
                    exclusion_hit += 1
                elif ar in ("insufficient_data", "manual_review"):
                    exclusion_insufficient += 1

        if exclusion_hit > 0:
            return "excluded"
        if inclusion_fail > 0 or inclusion_insufficient > 0 or exclusion_insufficient > 0:
            return "manual_review" if has_pending else "insufficient_data"
        if has_pending:
            return "manual_review"
        return "recommended"

    @staticmethod
    def compute_overall_score(evaluations: list) -> int:
        """加权综合评分计算 — Task 10.5"""
        if not evaluations:
            return 0

        total_weight = 0.0
        weighted_sum = 0.0

        for e in evaluations:
            ct = getattr(e, "criterion_type", "") if hasattr(e, "criterion_type") else e.get("criterion_type", "")
            ar = getattr(e, "ai_result", "") if hasattr(e, "ai_result") else e.get("ai_result", "")
            score = getattr(e, "confidence_score", 50) if hasattr(e, "confidence_score") else e.get("confidence_score", 50)

            weight = 1.0
            if ct == "exclusion" and ar == "exclusion_hit":
                weighted_sum += 0
                total_weight += weight * 2
                continue
            if ct == "inclusion" and ar == "fail":
                weighted_sum += 0
                total_weight += weight
                continue

            if ar in ("insufficient_data", "manual_review"):
                weighted_sum += (score or 50) * 0.5
            else:
                weighted_sum += (score or 50)
            total_weight += weight

        return round(weighted_sum / total_weight) if total_weight > 0 else 0
