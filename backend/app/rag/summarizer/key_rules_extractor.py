"""重点条例提取器。

调用 LLM 基于 KEY_RULES_PROMPT 提取 5-10 条关键条例，并解析为统一结构。
包含健壮的 JSON 解析逻辑以应对 LLM 返回格式不规范的情况。
"""
import json
import re
from typing import Any, Dict, List

from loguru import logger

from app.core.llm_factory import create_chat_llm
from app.rag.prompts.chat_prompts import KEY_RULES_PROMPT


# 输出格式约束：覆盖默认 prompt 的 JSON 结构，使其对齐业务字段
_SCHEMA_INSTRUCTION = """
请按以下 JSON 数组格式输出 5-10 条关键条例，每条包含以下字段：
[
  {
    "title": "条例标题（简短，10-20字）",
    "content": "条款具体内容",
    "source_location": "在文档中的位置（如：第3章第2节，无则留空字符串）",
    "category": "类别（如：奖学金、教务、住宿、考试等）",
    "importance_score": 重要性评分，0.0-1.0 之间的浮点数
  }
]

要求：
1. 严格输出 JSON 数组，不要输出任何解释性文本或 markdown 代码块。
2. 提取 5-10 条最具代表性的条例。
3. importance_score 反映该条例对学生的重要性程度。
"""


class KeyRulesExtractor:
    """重点条例提取器。"""

    MAX_INPUT_LENGTH = 4000
    MIN_RULES = 5
    MAX_RULES = 10

    def __init__(self) -> None:
        self._llm = None
        logger.debug("KeyRulesExtractor 已初始化")

    def _get_llm(self):
        """懒加载获取 LLM 实例。"""
        if self._llm is None:
            self._llm = create_chat_llm()
        return self._llm

    async def extract_rules(self, document_text: str) -> List[Dict[str, Any]]:
        """从文档中提取关键条例。

        Args:
            document_text: 文档全文文本。

        Returns:
            条例列表，元素为
            ``{title, content, source_location, category, importance_score}``。
            输入为空或解析失败时返回空列表。
        """
        if not document_text or not document_text.strip():
            logger.warning("文档内容为空，跳过条例提取")
            return []

        if len(document_text) > self.MAX_INPUT_LENGTH:
            logger.info(
                f"文档过长({len(document_text)}字)，截取前 {self.MAX_INPUT_LENGTH} 字提取条例"
            )
            document_text = document_text[: self.MAX_INPUT_LENGTH]

        try:
            base_prompt = KEY_RULES_PROMPT.format(content=document_text)
            full_prompt = f"{base_prompt}\n\n{_SCHEMA_INSTRUCTION}"
            response = await self._get_llm().ainvoke(full_prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            rules = self._parse_json_array(content)
            normalized = [
                self._normalize_rule(r) for r in rules if isinstance(r, dict)
            ]
            # 过滤掉缺字段的无效记录
            normalized = [
                r for r in normalized if r.get("title") and r.get("content")
            ]
            # 限制 5-10 条
            if len(normalized) > self.MAX_RULES:
                # 按重要性分数降序保留前 N 条
                normalized.sort(
                    key=lambda x: x.get("importance_score", 0.0), reverse=True
                )
                normalized = normalized[: self.MAX_RULES]
            logger.info(f"条例提取完成，共 {len(normalized)} 条")
            return normalized
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"条例提取失败: {exc}")
            raise

    @staticmethod
    def _parse_json_array(content: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的 JSON 数组，兼容 markdown 代码块与多余文本。

        Args:
            content: LLM 原始返回文本。

        Returns:
            解析得到的字典列表；解析失败返回空列表。
        """
        if not content:
            return []

        cleaned = content.strip()

        # 去除 markdown 代码块包裹
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\s*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)

        # 直接尝试解析
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except json.JSONDecodeError:
            pass

        # 退化为正则提取首个 JSON 数组
        match = re.search(r"\[\s*\{.*\}\s*\]", cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError as exc:
                logger.warning(f"正则提取后 JSON 解析失败: {exc}")

        logger.warning(
            f"无法解析为 JSON 数组，返回空列表。原始内容前 200 字: {content[:200]}"
        )
        return []

    @staticmethod
    def _normalize_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
        """将 LLM 返回的条例字段对齐到统一格式。

        兼容 prompt 默认字段命名（topic/rule/applicable_to/condition）
        与目标字段命名（title/content/source_location/category/importance_score）。
        """
        title = (
            rule.get("title")
            or rule.get("topic")
            or rule.get("主题")
            or ""
        )
        content = (
            rule.get("content")
            or rule.get("rule")
            or rule.get("条款内容")
            or rule.get("rule_content")
            or ""
        )
        source_location = (
            rule.get("source_location")
            or rule.get("location")
            or rule.get("applicable_to")
            or rule.get("condition")
            or ""
        )
        category = rule.get("category") or rule.get("类别") or ""

        importance_score = rule.get("importance_score")
        if importance_score is None:
            importance_score = 0.5
        try:
            importance_score = float(importance_score)
        except (TypeError, ValueError):
            importance_score = 0.5
        importance_score = max(0.0, min(1.0, importance_score))

        return {
            "title": str(title).strip(),
            "content": str(content).strip(),
            "source_location": str(source_location).strip() or None,
            "category": str(category).strip() or None,
            "importance_score": importance_score,
        }


# 模块级单例
key_rules_extractor = KeyRulesExtractor()
