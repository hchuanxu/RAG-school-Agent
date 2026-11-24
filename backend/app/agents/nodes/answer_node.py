"""回答生成节点。

基于检索上下文与对话历史生成回答，并对闲聊意图做对话式处理。
"""
import time
from typing import Any, Dict, List

from loguru import logger

from app.agents.state import AgentState, IntentType
from app.core.llm_factory import create_chat_llm
from app.rag.prompts.chat_prompts import ANSWER_GENERATION_PROMPT, SYSTEM_PROMPT


def _build_context(docs: List[dict]) -> str:
    """构建带来源标记的上下文（含知识库名称）。"""
    if not docs:
        return "(无相关资料)"
    parts: List[str] = []
    for idx, doc in enumerate(docs, start=1):
        content = (doc.get("content") or "").strip()
        metadata = doc.get("metadata") or {}
        file_name = doc.get("file_name") or metadata.get("file_name", "")
        kb_name = doc.get("knowledge_base") or metadata.get("knowledge_base", "")
        page = doc.get("page")
        page_info = f"，第{page}页" if page is not None else ""
        kb_info = f"（知识库：{kb_name}）" if kb_name else ""
        parts.append(f"[来源{idx}] {file_name}{page_info}{kb_info}\n{content}")
    return "\n\n".join(parts)


def _build_history(messages: List[dict]) -> str:
    """构建对话历史文本（取最近若干轮）。"""
    if not messages:
        return "(无历史对话)"
    lines: List[str] = []
    for msg in messages[-6:]:
        role = msg.get("role", "user")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        speaker = "用户" if role == "user" else "助手"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def _generate_casual_answer(llm, question: str, history: str) -> str:
    """闲聊场景：直接对话式回答，不依赖检索资料。"""
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"【对话历史】\n{history}\n\n"
        f"用户说：{question}\n\n"
        f"请以友善、简洁的口吻进行日常对话回应，无需引用资料。"
    )
    response = llm.invoke(prompt)
    return (response.content if hasattr(response, "content") else str(response)).strip()


def generate_answer(state: AgentState) -> Dict[str, Any]:
    """回答生成节点。"""
    start = time.perf_counter()
    question = state.get("question", "")
    intent = (state.get("intent") or "").strip().lower()
    docs: List[dict] = state.get("retrieved_docs") or []
    no_relevant = state.get("no_relevant_docs", False)
    messages: List[dict] = state.get("messages") or []

    # 闲聊：直接对话式回答
    if intent == IntentType.CASUAL_CHAT.value:
        try:
            llm = create_chat_llm()
            answer = _generate_casual_answer(llm, question, _build_history(messages))
            logger.info(f"闲聊回答生成完成, 长度={len(answer)}")
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {"answer": answer, "generation_latency_ms": latency_ms}
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"闲聊回答生成异常: {exc}")
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {"answer": "您好，我是校园智能问答助手，请问有什么可以帮您？", "generation_latency_ms": latency_ms}

    # 无相关文档：返回兜底回答
    if no_relevant:
        logger.info("无相关文档，返回兜底回答")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"answer": "抱歉，知识库中暂无相关信息。", "generation_latency_ms": latency_ms}

    # 基于检索资料生成回答
    context = _build_context(docs)
    history = _build_history(messages)
    try:
        llm = create_chat_llm()
        prompt = ANSWER_GENERATION_PROMPT.format(question=question, context=context)
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"【对话历史】\n{history}\n\n"
            f"{prompt}\n\n"
            f"请确保在回答末尾统一列出「📚 知识库来源」区域，注明文件名、页码和所属知识库名称。"
        )
        response = llm.invoke(full_prompt)
        answer = (response.content if hasattr(response, "content") else str(response)).strip()
        logger.info(f"回答生成完成, 长度={len(answer)}")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"answer": answer, "generation_latency_ms": latency_ms}
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"回答生成异常: {exc}")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return {"answer": "抱歉，回答生成失败，请稍后重试。", "generation_latency_ms": latency_ms}
