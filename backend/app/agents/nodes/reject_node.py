"""拒绝节点。

根据意图与审核结果设置拒绝原因，并生成友好的拒绝消息。
"""
from typing import Any, Dict

from loguru import logger

from app.agents.state import AgentState, IntentType


_INVALID_MESSAGE = (
    "抱歉，您的问题含义不清，请尝试更明确、具体地描述您的问题，"
    "我将尽力为您解答。"
)
_OUT_OF_SCOPE_MESSAGE = (
    "抱歉，我是校园智能问答助手，仅能回答与校园政策、教务、奖学金、"
    "校园生活等相关的问题，请提出校园相关的问题。"
)
_REVIEW_FAIL_MESSAGE = (
    "抱歉，当前无法给出可靠回答，建议您咨询学校相关部门或查阅官方最新文件。"
)
_GENERIC_MESSAGE = "抱歉，暂无法回答您的问题，请稍后重试或换一种方式提问。"


def reject_question(state: AgentState) -> Dict[str, Any]:
    """拒绝节点。"""
    intent = (state.get("intent") or "").strip().lower()
    has_hallucination = state.get("has_hallucination", False)
    has_sensitive = state.get("has_sensitive_content", False)

    if has_hallucination or has_sensitive:
        reason = "审核未通过：回答存在幻觉或敏感内容"
        message = _REVIEW_FAIL_MESSAGE
    elif intent == IntentType.INVALID.value:
        reason = "无效问题"
        message = _INVALID_MESSAGE
    elif intent == IntentType.OUT_OF_SCOPE.value:
        reason = "超出知识范围"
        message = _OUT_OF_SCOPE_MESSAGE
    else:
        reason = "无法回答"
        message = _GENERIC_MESSAGE

    logger.info(f"拒绝问题: reason={reason}, intent={intent}")
    return {
        "should_reject": True,
        "reject_reason": reason,
        "final_answer": message,
    }
