"""LangGraph 状态图构建。

定义校园智能问答多智能体工作流的节点、边与条件路由，
并编译为可执行图。提供 ``create_campus_agent`` 与 ``run_agent``。
"""
import time
from typing import Any, Dict, List, Optional

from langgraph.graph import END, StateGraph
from loguru import logger

from app.agents.nodes import (
    extract_citations,
    generate_answer,
    recognize_intent,
    reject_question,
    retrieve_documents,
    review_answer,
    route_intent,
)
from app.agents.nodes.review_node import MAX_RETRIES
from app.agents.state import AgentState


def _after_review(state: AgentState) -> str:
    """审核后路由。

    - 审核通过 -> 结束
    - 审核未通过且重试次数超过上限 -> 拒绝
    - 审核未通过且仍可重试 -> 回到回答节点重新生成
    """
    if state.get("review_passed"):
        return "end"
    if state.get("retry_count", 0) > MAX_RETRIES:
        return "reject"
    return "answer"


def create_campus_agent():
    """创建并编译校园智能问答工作流。

    注意：LangGraph 0.2.x 不允许节点名与状态键同名，因此将
    ``intent``/``answer`` 节点命名为 ``intent_classifier``/``answer_generator``，
    路由函数返回值仍为 ``retrieve``/``answer``/``reject``，通过条件边映射字典转换。
    """
    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node("intent_classifier", recognize_intent)
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("citation", extract_citations)
    workflow.add_node("answer_generator", generate_answer)
    workflow.add_node("review", review_answer)
    workflow.add_node("reject", reject_question)

    # START -> 意图识别
    workflow.set_entry_point("intent_classifier")

    # 意图识别 -> 条件路由（retrieve / answer / reject）
    workflow.add_conditional_edges(
        "intent_classifier",
        route_intent,
        {
            "retrieve": "retrieve",
            "answer": "answer_generator",
            "reject": "reject",
        },
    )

    # 检索 -> 溯源 -> 回答
    workflow.add_edge("retrieve", "citation")
    workflow.add_edge("citation", "answer_generator")

    # 回答 -> 审核
    workflow.add_edge("answer_generator", "review")

    # 审核 -> 结束 / 回答（重试）/ 拒绝
    workflow.add_conditional_edges(
        "review",
        _after_review,
        {
            "end": END,
            "answer": "answer_generator",
            "reject": "reject",
        },
    )

    # 拒绝 -> 结束
    workflow.add_edge("reject", END)

    agent = workflow.compile()
    logger.info("校园智能问答工作流已编译")
    return agent


def run_agent(
    agent,
    question: str,
    messages: Optional[List[dict]] = None,
    knowledge_base_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """运行工作流的辅助函数。

    Args:
        agent: 由 :func:`create_campus_agent` 编译得到的图。
        question: 当前用户问题。
        messages: 对话历史，元素为 ``{"role": "user"/"assistant", "content": "..."}``。
        knowledge_base_ids: 指定检索的知识库（集合名）列表，为空则使用默认知识库。

    Returns:
        工作流执行完成后的最终状态字典。
    """
    initial_state: Dict[str, Any] = {
        "messages": messages or [],
        "conversation_id": "",
        "question": question,
        "intent": "",
        "intent_confidence": 0.0,
        "retrieved_docs": [],
        "no_relevant_docs": False,
        "citations": [],
        "answer": "",
        "review_passed": False,
        "has_hallucination": False,
        "has_sensitive_content": False,
        "review_suggestions": "",
        "final_answer": "",
        "should_reject": False,
        "reject_reason": "",
        "knowledge_base_ids": knowledge_base_ids or [],
        "retry_count": 0,
        "retrieval_latency_ms": 0,
        "generation_latency_ms": 0,
        "agent_start_time": 0.0,
    }
    initial_state["agent_start_time"] = time.time()
    result = agent.invoke(initial_state)
    logger.info(
        f"工作流执行完成: intent={result.get('intent')}, "
        f"review_passed={result.get('review_passed')}, "
        f"should_reject={result.get('should_reject')}"
    )
    return result
