"""路由节点。

根据意图识别结果决定下一步流转的节点名。
"""
from typing import Any

from loguru import logger

from app.agents.state import AgentState, IntentType


def route_intent(state: AgentState) -> str:
    """根据意图返回下一步节点名。

    - casual_chat -> "answer"（直接回答）
    - invalid / out_of_scope -> "reject"（拒绝）
    - 其他 -> "retrieve"（检索）
    """
    intent = (state.get("intent") or "").strip().lower()
    logger.info(f"路由判断: intent={intent}")

    if intent == IntentType.CASUAL_CHAT.value:
        return "answer"
    if intent in (IntentType.INVALID.value, IntentType.OUT_OF_SCOPE.value):
        return "reject"
    return "retrieve"
