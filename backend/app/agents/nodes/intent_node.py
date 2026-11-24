"""意图识别节点。

调用 LLM 对用户问题进行意图分类，支持 JSON 与纯文本两种返回格式解析。
"""
import json
import re
from typing import Any, Dict, Tuple

from loguru import logger

from app.agents.state import AgentState, IntentType
from app.core.llm_factory import create_chat_llm
from app.rag.prompts.chat_prompts import INTENT_CLASSIFICATION_PROMPT, INTENT_LABELS


_VALID_INTENTS = {intent.value for intent in IntentType}


def _parse_intent_response(text: str) -> Tuple[str, float]:
    """解析 LLM 返回，提取 intent 与 confidence。

    优先尝试 JSON 解析；失败则退化为从纯文本中匹配已知意图标识。
    """
    text = (text or "").strip()

    # 尝试 JSON 解析
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                intent = str(data.get("intent", "")).strip().lower()
                try:
                    confidence = float(data.get("confidence", 0.8))
                except (TypeError, ValueError):
                    confidence = 0.8
                return intent, confidence
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # 退化：从纯文本中提取已知类别标识
    lower_text = text.lower()
    matched = None
    for intent_value in _VALID_INTENTS:
        if intent_value in lower_text:
            matched = intent_value
            break
    if not matched:
        tokens = re.split(r"[\s,，。:：、]+", lower_text)
        candidate = tokens[0].strip() if tokens else ""
        if candidate in _VALID_INTENTS:
            matched = candidate
    if matched:
        return matched, 0.8
    return "", 0.0


def recognize_intent(state: AgentState) -> Dict[str, Any]:
    """意图识别节点。"""
    question = (state.get("question") or "").strip()

    # 问题过短或无意义，直接判定为 invalid
    if len(question) < 2:
        logger.info(f"问题过短，直接判定 invalid: {question!r}")
        return {
            "intent": IntentType.INVALID.value,
            "intent_confidence": 1.0,
        }

    try:
        llm = create_chat_llm()
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            user_input=question,
            campus_policy=INTENT_LABELS["campus_policy"],
            academic_affairs=INTENT_LABELS["academic_affairs"],
            scholarship=INTENT_LABELS["scholarship"],
            campus_life=INTENT_LABELS["campus_life"],
            casual_chat=INTENT_LABELS["casual_chat"],
            invalid=INTENT_LABELS["invalid"],
            out_of_scope=INTENT_LABELS["out_of_scope"],
        )
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        intent, confidence = _parse_intent_response(content)

        if not intent:
            logger.warning(f"意图解析失败，默认 casual_chat。原始返回: {content!r}")
            intent = IntentType.CASUAL_CHAT.value
            confidence = 0.3

        logger.info(f"意图识别结果: {intent} (confidence={confidence})")
        return {"intent": intent, "intent_confidence": confidence}
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"意图识别异常，默认 casual_chat: {exc}")
        return {
            "intent": IntentType.CASUAL_CHAT.value,
            "intent_confidence": 0.0,
        }
