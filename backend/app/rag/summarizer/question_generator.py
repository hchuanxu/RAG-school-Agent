"""考点生成器。

调用 LLM 基于 QUESTION_GEN_PROMPT 生成 5-10 个考点题目，并解析为统一结构。
难度分级：基础 / 进阶 / 拓展。
"""
import json
import re
from typing import Any, Dict, List

from loguru import logger

from app.core.llm_factory import create_chat_llm
from app.rag.prompts.chat_prompts import QUESTION_GEN_PROMPT


# 输出格式约束：覆盖默认 prompt 的 JSON 结构，对齐业务字段
_SCHEMA_INSTRUCTION = """
请按以下 JSON 数组格式输出 5-10 个考点题目，每条包含以下字段：
[
  {
    "question": "题干",
    "answer": "标准答案（可包含简要解析）",
    "difficulty": "难度，取值之一：基础 / 进阶 / 拓展",
    "category": "考点类别（如：奖学金、教务、住宿、考试等）",
    "source_location": "在文档中的位置（如：第3章第2节，无则留空字符串）"
  }
]

要求：
1. 严格输出 JSON 数组，不要输出任何解释性文本或 markdown 代码块。
2. 生成 5-10 个覆盖文档关键知识点的考点。
3. 难度分布大致为：基础 50%、进阶 30%、拓展 20%。
4. 答案须能从原文定位，不编造未提供的信息。
"""


class QuestionGenerator:
    """考点生成器。"""

    MAX_INPUT_LENGTH = 4000
    MIN_QUESTIONS = 5
    MAX_QUESTIONS = 10
    VALID_DIFFICULTIES = ("基础", "进阶", "拓展")

    def __init__(self) -> None:
        self._llm = None
        logger.debug("QuestionGenerator 已初始化")

    def _get_llm(self):
        """懒加载获取 LLM 实例。"""
        if self._llm is None:
            self._llm = create_chat_llm()
        return self._llm

    async def generate_questions(
        self, document_text: str
    ) -> List[Dict[str, Any]]:
        """基于文档生成考点题目。

        Args:
            document_text: 文档全文文本。

        Returns:
            考点列表，元素为
            ``{question, answer, difficulty, category, source_location}``。
            输入为空或解析失败时返回空列表。
        """
        if not document_text or not document_text.strip():
            logger.warning("文档内容为空，跳过考点生成")
            return []

        if len(document_text) > self.MAX_INPUT_LENGTH:
            logger.info(
                f"文档过长({len(document_text)}字)，截取前 {self.MAX_INPUT_LENGTH} 字生成考点"
            )
            document_text = document_text[: self.MAX_INPUT_LENGTH]

        try:
            base_prompt = QUESTION_GEN_PROMPT.format(content=document_text)
            full_prompt = f"{base_prompt}\n\n{_SCHEMA_INSTRUCTION}"
            response = await self._get_llm().ainvoke(full_prompt)
            content = (
                response.content if hasattr(response, "content") else str(response)
            )
            questions = self._parse_json_array(content)
            normalized = [
                self._normalize_question(q)
                for q in questions
                if isinstance(q, dict)
            ]
            # 过滤掉缺字段的无效记录
            normalized = [
                q for q in normalized if q.get("question") and q.get("answer")
            ]
            # 限制 5-10 个
            if len(normalized) > self.MAX_QUESTIONS:
                normalized = normalized[: self.MAX_QUESTIONS]
            logger.info(f"考点生成完成，共 {len(normalized)} 个")
            return normalized
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"考点生成失败: {exc}")
            # 考点生成失败不应阻断摘要与条例的保存，返回空列表
            return []

    @staticmethod
    def _parse_json_array(content: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的 JSON 数组，兼容 markdown 代码块、多余文本与部分截断。

        解析策略（逐级降级）：
        1. 清理 markdown 代码块后直接 json.loads
        2. 修复常见 JSON 格式错误后重试（尾逗号、截断等）
        3. 用 raw_decode 解析首个完整 JSON 值
        4. 逐个提取 {...} 对象，跳过损坏的条目，尽量挽救有效考点
        """
        if not content:
            return []

        cleaned = content.strip()

        # 去除 markdown 代码块包裹
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\s*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned)

        # 策略 1：直接解析
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except json.JSONDecodeError:
            pass

        # 策略 2：修复常见 JSON 格式错误
        repaired = QuestionGenerator._repair_json(cleaned)
        if repaired != cleaned:
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, list):
                    logger.info("JSON 修复后解析成功")
                    return parsed
            except json.JSONDecodeError:
                pass

        # 策略 3：raw_decode 解析首个完整 JSON 值
        try:
            decoder = json.JSONDecoder()
            # 找到第一个 '[' 或 '{'
            for i, ch in enumerate(cleaned):
                if ch in "[{":
                    obj, _ = decoder.raw_decode(cleaned[i:])
                    if isinstance(obj, list):
                        return obj
                    if isinstance(obj, dict):
                        return [obj]
                    break
        except (json.JSONDecodeError, ValueError):
            pass

        # 策略 4：逐个提取 {...} 对象，跳过损坏条目
        salvaged = QuestionGenerator._extract_individual_objects(cleaned)
        if salvaged:
            logger.info(f"部分挽救解析成功，提取到 {len(salvaged)} 个有效对象")
            return salvaged

        logger.warning(
            f"无法解析为 JSON 数组，返回空列表。原始内容前 200 字: {content[:200]}"
        )
        return []

    @staticmethod
    def _repair_json(text: str) -> str:
        """修复 LLM 输出中常见的 JSON 格式错误。"""
        # 1. 移除 } 或 ] 前的尾逗号
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # 2. 补全截断的数组（如果以 { 结尾但缺少 ] ）
        if text.rstrip().endswith("}"):
            brace_count = text.count("{") - text.count("}")
            bracket_count = text.count("[") - text.count("]")
            if bracket_count > 0:
                text = text.rstrip() + "]" * bracket_count
        # 3. 移除控制字符
        text = re.sub(r"[\x00-\x1f]", "", text)
        return text

    @staticmethod
    def _extract_individual_objects(text: str) -> List[Dict[str, Any]]:
        """从文本中逐个提取 {...} JSON 对象，跳过损坏的条目。"""
        results: List[Dict[str, Any]] = []
        depth = 0
        start = -1
        decoder = json.JSONDecoder()

        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    fragment = text[start : i + 1]
                    try:
                        obj = json.loads(fragment)
                        if isinstance(obj, dict):
                            results.append(obj)
                    except json.JSONDecodeError:
                        # 尝试修复后解析
                        repaired = QuestionGenerator._repair_json(fragment)
                        try:
                            obj = json.loads(repaired)
                            if isinstance(obj, dict):
                                results.append(obj)
                        except json.JSONDecodeError:
                            pass
                    start = -1

        return results

    @staticmethod
    def _normalize_question(q: Dict[str, Any]) -> Dict[str, Any]:
        """将 LLM 返回的考点字段对齐到统一格式。

        兼容 prompt 默认字段命名（type/question/options/answer/explanation）
        与目标字段命名（question/answer/difficulty/category/source_location）。
        """
        question = q.get("question") or q.get("题干") or ""

        # 合并 answer 与 explanation
        answer = q.get("answer") or ""
        explanation = q.get("explanation") or q.get("解析") or ""
        if explanation and explanation not in answer:
            answer = f"{answer}\n解析：{explanation}".strip()

        # 难度归一化
        difficulty = (q.get("difficulty") or q.get("难度") or "基础").strip()
        # 兼容英文难度标识
        difficulty_map = {
            "easy": "基础",
            "basic": "基础",
            "medium": "进阶",
            "advanced": "进阶",
            "hard": "拓展",
            "expert": "拓展",
        }
        difficulty_lower = difficulty.lower()
        if difficulty_lower in difficulty_map:
            difficulty = difficulty_map[difficulty_lower]
        if difficulty not in QuestionGenerator.VALID_DIFFICULTIES:
            # 模糊匹配
            if "基础" in difficulty or "简单" in difficulty:
                difficulty = "基础"
            elif "进阶" in difficulty or "中等" in difficulty:
                difficulty = "进阶"
            elif "拓展" in difficulty or "高" in difficulty:
                difficulty = "拓展"
            else:
                difficulty = "基础"

        category = q.get("category") or q.get("类别") or q.get("type") or ""
        source_location = (
            q.get("source_location") or q.get("location") or ""
        )

        return {
            "question": str(question).strip(),
            "answer": str(answer).strip(),
            "difficulty": difficulty,
            "category": str(category).strip() or None,
            "source_location": str(source_location).strip() or None,
        }


# 模块级单例
question_generator = QuestionGenerator()
