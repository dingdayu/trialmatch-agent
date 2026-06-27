"""提示词构建器 — 对应 Task 10.2
为 AI 匹配引擎构建结构化的提示词"""

from __future__ import annotations

from typing import List, Optional


class PromptBuilder:
    """AI 匹配提示词构建器"""

    SYSTEM_ROLE = """你是一位专业的临床试验受试者筛选专家。你需要根据临床入排标准，仔细分析受试者的医疗资料，判断受试者是否符合每条标准。

请严格遵守以下规则：
1. 逐条分析每条标准，给出独立的匹配结论
2. 结论必须基于受试者资料中的客观证据
3. 对于每条判断，必须引用具体的原文作为证据
4. 如果资料不足以判断，请明确标注为"资料不足"
5. 排除标准命中任意一条即判定为不符合
6. 入选标准需全部满足（或资料不足以判断）才算通过"""

    @staticmethod
    def build_criterion_evaluation_prompt(
        criterion: dict,
        subject_info: dict,
        chunks_text: str,
        ai_prompt: Optional[str] = None,
    ) -> str:
        """构建单条标准匹配判断的提示词"""
        criterion_type_label = "入选标准" if criterion.get("criterion_type") == "inclusion" else "排除标准"

        prompt = f"""## 项目背景
{ai_prompt or "无特殊说明"}

## 受试者信息
- 编号: {subject_info.get("subject_no", "")}
- 性别: {subject_info.get("gender", "")}
- 年龄: {subject_info.get("age", "")}
- 诊断: {subject_info.get("diagnosis", "")}
- 研究中心: {subject_info.get("site_name", "")}

## 受试者医疗资料（摘要）
{chunks_text[:5000]}

## {criterion_type_label}
- 标准编号: {criterion.get("criterion_code", "")}
- 标准内容: {criterion.get("criterion_text", "")}
- 标准说明: {criterion.get("criterion_explanation", "") or "无"}
- AI 辅助指令: {criterion.get("ai_instruction", "") or "无"}

## 判断要求
请根据以上受试者资料，判断该受试者是否满足此{criterion_type_label}。

请按以下 JSON 格式输出：

```json
{{
    "result": "pass|fail|exclusion_hit|exclusion_not_hit|insufficient_data|manual_review",
    "confidence": 0-100,
    "rationale": "详细的判断理由，包含推理过程",
    "citations": [
        {{
            "quoted_text": "引用的原文片段",
            "extracted_fact": "从原文提取的关键事实",
            "relevance_explanation": "为什么这个证据与标准相关"
        }}
    ],
    "missing_info": ["缺少的关键信息列表"]
}}
```

结果类型说明：
- 入选标准: pass(满足), fail(不满足), insufficient_data(资料不足), manual_review(需人工复核)
- 排除标准: exclusion_hit(命中排除), exclusion_not_hit(未命中), insufficient_data(资料不足), manual_review(需人工复核)
"""
        return prompt

    @staticmethod
    def build_batch_subject_info(
        subject: dict,
        project: dict,
        criteria_list: List[dict],
    ) -> str:
        """构建批量初筛的系统提示"""
        inclusion_criteria = [c for c in criteria_list if c.get("criterion_type") == "inclusion"]
        exclusion_criteria = [c for c in criteria_list if c.get("criterion_type") == "exclusion"]

        prompt = f"""## 项目信息
- 项目编号: {project.get("project_no", "")}
- 研究名称: {project.get("study_name", "")}
- 适应症: {project.get("indication", "")}

## AI 指令
{project.get("ai_prompt", "无")}

## 入选标准 ({len(inclusion_criteria)} 条)
"""
        for c in inclusion_criteria:
            prompt += f"- [{c.get('criterion_code')}] {c.get('criterion_text')}\n"

        prompt += f"\n## 排除标准 ({len(exclusion_criteria)} 条)\n"
        for c in exclusion_criteria:
            prompt += f"- [{c.get('criterion_code')}] {c.get('criterion_text')}\n"

        prompt += f"""
## 受试者信息
- 编号: {subject.get('subject_no', '')}
- 性别: {subject.get('gender', '')}
- 年龄: {subject.get('age', '')}
- 诊断: {subject.get('diagnosis', '')}
"""
        return prompt
