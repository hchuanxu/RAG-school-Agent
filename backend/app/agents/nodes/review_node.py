"""审核节点。

使用 LLM 检查幻觉，并结合敏感词检测判断回答是否合规；
审核未通过时累计重试计数，达到上限后交由拒绝节点处理。
"""
import json
import re
from typing import Any, Dict, List

from loguru import logger

from app.agents.state import AgentState
from app.core.llm_factory import create_chat_llm
from app.rag.prompts.chat_prompts import REVIEW_PROMPT


# 最大重试次数（仅允许 1 次重新生成）
MAX_RETRIES = 1

# 敏感词列表（示例，可按需扩展）
SENSITIVE_WORDS: List[str] = [
    "反动", "暴力", "色情", "赌博", "毒品", "诈骗",
    "传销", "邪教", "恐怖", "武器", "炸弹", "自杀",
    "政治敏感", "反华", "港独", "疆独", "藏独",
]


def _build_context(docs: List[dict]) -> str:
    """构建审核用上下文。"""
    if not docs:
        return "(无相关资料)"
    parts: List[str] = []
    for idx, doc in enumerate(docs, start=1):
        content = (doc.get("content") or "").strip()
        parts.append(f"[来源{idx}] {content}")
    return "\n\n".join(parts)


def _check_sensitive(text: str) -> bool:
    """简单敏感词检测。"""
    lower = text.lower()
    return any(word in text or word.lower() in lower for word in SENSITIVE_WORDS)


def _parse_review_response(text: str) -> dict:
    """解析 LLM 审核返回的 JSON。"""
    text = (text or "").strip()
    # 提取首个 JSON 对象，兼容 markdown 代码块包裹
    match = re.search(r"\{.*\}", text, re.DOTALL)
    json_str = match.group(0) if match else text
    try:
        data = json.loads(json_str)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return {}


def review_answer(state: AgentState) -> Dict[str, Any]:
    """审核节点。"""
    answer = state.get("answer", "")
    question = state.get("question", "")
    docs: List[dict] = state.get("retrieved_docs") or []
    no_relevant = state.get("no_relevant_docs", False)
    retry_count = state.get("retry_count", 0)

    # 无相关文档时的兜底回答直接放行
    if no_relevant:
        return {
            "review_passed": True,
            "has_hallucination": False,
            "has_sensitive_content": False,
            "review_suggestions": "",
            "final_answer": answer,
        }

    has_sensitive = _check_sensitive(answer)
    has_hallucination = False
    suggestions: List[str] = []

    # LLM 审核幻觉与质量
    try:
        llm = create_chat_llm()
        context = _build_context(docs)
        prompt = REVIEW_PROMPT.format(
            question=question, answer=answer, context=context
        )
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        data = _parse_review_response(content)

        llm_pass = bool(data.get("pass", True))
        issues = data.get("issues", []) or []
        suggestion = data.get("suggestion", "") or ""
        if suggestion:
            suggestions.append(suggestion)
        if issues:
            suggestions.append("问题：" + "；".join(str(i) for i in issues))
        if not llm_pass:
            has_hallucination = True
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"审核 LLM 调用异常，默认通过: {exc}")

    review_passed = (not has_hallucination) and (not has_sensitive)
    review_suggestions = " ".join(suggestions).strip()

    if review_passed:
        logger.info("审核通过")
        return {
            "review_passed": True,
            "has_hallucination": has_hallucination,
            "has_sensitive_content": has_sensitive,
            "review_suggestions": review_suggestions,
            "final_answer": answer,
        }

    # 审核未通过，累计重试计数
    retry_count += 1
    logger.info(
        f"审核未通过: hallucination={has_hallucination}, "
        f"sensitive={has_sensitive}, retry_count={retry_count}"
    )
    return {
        "review_passed": False,
        "has_hallucination": has_hallucination,
        "has_sensitive_content": has_sensitive,
        "review_suggestions": review_suggestions,
        "retry_count": retry_count,
    }
