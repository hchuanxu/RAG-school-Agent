"""对话服务。

封装会话管理、调用 LangGraph 智能体进行问答（非流式与 SSE 流式）以及
对话历史查询等功能。
"""
import asyncio
import json
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import create_campus_agent, run_agent
from app.analytics.question_recorder import question_recorder
from app.core.exceptions import (
    BusinessException,
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.metrics.answer_metrics import answer_metrics
from app.metrics.latency_metrics import latency_metrics
from app.metrics.recall_metrics import recall_metrics
from app.models.chat import ChatMessage, ChatSession
from app.models.knowledge_base import KnowledgeBase
from app.schemas.chat import (
    ChatMessageResponse,
    ChatSessionResponse,
)
from app.schemas.common import PaginatedResponse

# 智能体单例（懒加载）
_agent_instance = None


def _get_agent():
    """获取已编译的校园智能体单例。"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_campus_agent()
        logger.info("校园智能体单例已创建")
    return _agent_instance


# 按句子/换行切分用于流式输出的最小单元
_SENTENCE_RE = re.compile(r"(?<=[。！？!?\.])\s+|\n+")


def _split_for_stream(text: str) -> List[str]:
    """将完整回答切分为可流式输出的片段。"""
    if not text:
        return []
    parts = [p for p in _SENTENCE_RE.split(text) if p]
    if len(parts) <= 1:
        # 退化为按固定长度切分
        step = 24
        return [text[i : i + step] for i in range(0, len(text), step)]
    return parts


class ChatService:
    """对话服务。"""

    async def create_session(
        self, db: AsyncSession, user_id: int, title: str = "新对话"
    ) -> ChatSessionResponse:
        """创建新的对话会话。"""
        session = ChatSession(user_id=user_id, title=title[:256] or "新对话")
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info(f"会话已创建: id={session.id}, user_id={user_id}")
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0,
        )

    async def chat(
        self,
        db: AsyncSession,
        user_id: int,
        question: str,
        session_id: Optional[int] = None,
        knowledge_base_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """非流式对话。

        Returns:
            包含 answer / citations / session_id / message_id 的字典。
        """
        session = await self._ensure_session(db, user_id, session_id, question)
        history = await self._load_history(db, session.id)
        collection_names = await self._resolve_collection_names(
            db, knowledge_base_ids
        )

        agent = _get_agent()
        result = await asyncio.to_thread(
            run_agent, agent, question, history, collection_names
        )

        answer = result.get("final_answer") or result.get("answer") or ""
        citations = result.get("citations") or []
        intent = result.get("intent")
        no_relevant = result.get("no_relevant_docs", False)

        # 保存用户与助手消息
        user_msg = ChatMessage(
            session_id=session.id, role="user", content=question
        )
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            citations=citations,
        )
        db.add_all([user_msg, assistant_msg])
        await db.commit()
        await db.refresh(assistant_msg)

        # 记录问题到 QuestionLog（用于仪表盘统计）
        try:
            await question_recorder.record(
                db,
                question=question,
                intent=intent if isinstance(intent, str) else None,
                is_valid=not no_relevant,
                user_id=user_id,
                session_id=session.id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"记录问题失败（不影响对话）: {exc}")

        # 指标采集
        await self._record_metrics(
            db, result, session.id, assistant_msg.id, question, answer, citations
        )

        logger.info(
            f"对话完成: session_id={session.id}, msg_id={assistant_msg.id}, "
            f"answer_len={len(answer)}, citations={len(citations)}"
        )
        return {
            "answer": answer,
            "citations": citations,
            "session_id": session.id,
            "message_id": assistant_msg.id,
        }

    async def chat_stream(
        self,
        db: AsyncSession,
        user_id: int,
        question: str,
        session_id: Optional[int] = None,
        knowledge_base_ids: Optional[List[int]] = None,
    ) -> AsyncGenerator[str, None]:
        """SSE 流式对话。

        生成器产出符合 SSE 协议的字符串（``data: {...}\\n\\n``）。
        由于底层 agent 不支持流式，先完整执行再分片输出。
        """
        session = await self._ensure_session(db, user_id, session_id, question)
        request_start = time.perf_counter()
        history = await self._load_history(db, session.id)
        collection_names = await self._resolve_collection_names(
            db, knowledge_base_ids
        )

        # 先发送会话信息
        yield self._sse({"type": "session", "session_id": session.id})

        try:
            agent = _get_agent()
            result = await asyncio.to_thread(
                run_agent, agent, question, history, collection_names
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"流式对话执行失败: {exc}")
            yield self._sse({"type": "error", "message": str(exc)})
            return

        answer = result.get("final_answer") or result.get("answer") or ""
        citations = result.get("citations") or []
        intent = result.get("intent")
        no_relevant = result.get("no_relevant_docs", False)

        # 持久化消息
        user_msg = ChatMessage(
            session_id=session.id, role="user", content=question
        )
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            citations=citations,
        )
        db.add_all([user_msg, assistant_msg])
        await db.commit()
        await db.refresh(assistant_msg)

        # 记录问题到 QuestionLog（用于仪表盘统计）
        try:
            await question_recorder.record(
                db,
                question=question,
                intent=intent if isinstance(intent, str) else None,
                is_valid=not no_relevant,
                user_id=user_id,
                session_id=session.id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"记录问题失败（不影响对话）: {exc}")

        # 指标采集（端到端延迟在流式输出完成后单独记录）
        await self._record_metrics(
            db, result, session.id, assistant_msg.id, question, answer, citations
        )

        # 记录 TTFT
        ttft_ms = int((time.perf_counter() - request_start) * 1000)
        try:
            await latency_metrics.record_ttft(db, session.id, assistant_msg.id, ttft_ms)
        except Exception as exc:
            logger.warning(f"记录 TTFT 失败: {exc}")

        # 分片输出回答
        for chunk in _split_for_stream(answer):
            yield self._sse(
                {"type": "token", "content": chunk, "message_id": assistant_msg.id}
            )

        # 输出引用溯源
        yield self._sse(
            {
                "type": "citations",
                "citations": citations,
                "message_id": assistant_msg.id,
            }
        )
        yield self._sse({"type": "done"})

        # 记录端到端延迟
        e2e_ms = int((time.perf_counter() - request_start) * 1000)
        try:
            await latency_metrics.record_e2e_latency(
                db, session.id, assistant_msg.id, e2e_ms,
                retrieval_ms=result.get("retrieval_latency_ms", 0) or 0,
                generation_ms=result.get("generation_latency_ms", 0) or 0,
            )
        except Exception as exc:
            logger.warning(f"记录端到端延迟失败: {exc}")

    async def get_history(
        self, db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[ChatSessionResponse]:
        """分页获取当前用户的会话列表。"""
        page = max(page, 1)
        page_size = max(min(page_size, 100), 1)

        total_result = await db.execute(
            select(func.count(ChatSession.id)).where(
                ChatSession.user_id == user_id
            )
        )
        total = total_result.scalar_one()

        # 会话列表 + 消息数（左连接聚合）
        result = await db.execute(
            select(ChatSession, func.count(ChatMessage.id).label("message_count"))
            .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id)
            .group_by(ChatSession.id)
            .order_by(ChatSession.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = result.all()

        total_pages = (total + page_size - 1) // page_size if total else 0
        items = [
            ChatSessionResponse(
                id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=int(msg_count or 0),
            )
            for session, msg_count in rows
        ]
        return PaginatedResponse[ChatSessionResponse](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_session(
        self, db: AsyncSession, user_id: int, session_id: int
    ) -> List[ChatMessageResponse]:
        """获取指定会话的消息列表。"""
        session = await self._get_owned_session(db, user_id, session_id)
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.id.asc())
        )
        messages = result.scalars().all()
        return [
            ChatMessageResponse(
                role=m.role,
                content=m.content,
                citations=m.citations,
                created_at=m.created_at,
            )
            for m in messages
        ]

    async def delete_session(
        self, db: AsyncSession, user_id: int, session_id: int
    ) -> None:
        """删除指定会话。"""
        session = await self._get_owned_session(db, user_id, session_id)
        await db.delete(session)
        await db.commit()
        logger.info(f"会话已删除: id={session_id}, user_id={user_id}")

    async def rename_session(
        self, db: AsyncSession, user_id: int, session_id: int, title: str
    ) -> ChatSessionResponse:
        """重命名指定会话。"""
        session = await self._get_owned_session(db, user_id, session_id)
        session.title = title.strip()[:256] or "新对话"
        await db.commit()
        await db.refresh(session)
        logger.info(f"会话已重命名: id={session_id}, title={session.title}")
        return ChatSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=0,
        )

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    async def _ensure_session(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int],
        question: str,
    ) -> ChatSession:
        """获取或创建会话。"""
        if session_id is not None:
            return await self._get_owned_session(db, user_id, session_id)
        title = question.strip()[:30] or "新对话"
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        logger.info(f"自动创建会话: id={session.id}, title={title}")
        return session

    async def _get_owned_session(
        self, db: AsyncSession, user_id: int, session_id: int
    ) -> ChatSession:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise ResourceNotFoundError("会话不存在或无权访问")
        return session

    async def _load_history(
        self, db: AsyncSession, session_id: int
    ) -> List[dict]:
        """加载会话历史并转换为 agent 期望的格式。"""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
        )
        messages = result.scalars().all()
        return [
            {"role": m.role, "content": m.content} for m in messages
        ]

    async def _resolve_collection_names(
        self,
        db: AsyncSession,
        knowledge_base_ids: Optional[List[int]],
    ) -> List[str]:
        """将知识库 ID 列表转换为 ChromaDB 集合名列表。

        传入空列表或 None 时返回所有公开知识库的集合名。
        """
        if not knowledge_base_ids:
            # 未指定知识库时，搜索所有公开知识库
            result = await db.execute(
                select(KnowledgeBase.collection_name).where(
                    KnowledgeBase.is_public.is_(True)
                )
            )
            names = [row[0] for row in result.all()]
            if not names:
                logger.warning("系统中没有公开知识库，检索将返回空结果")
            else:
                logger.info(f"未指定知识库，搜索所有公开知识库: {len(names)} 个")
            return names
        result = await db.execute(
            select(KnowledgeBase.collection_name).where(
                KnowledgeBase.id.in_(knowledge_base_ids)
            )
        )
        names = [row[0] for row in result.all()]
        if not names:
            logger.warning(
                f"未找到对应的知识库: ids={knowledge_base_ids}"
            )
        return names

    async def _record_metrics(
        self,
        db: AsyncSession,
        result: Dict[str, Any],
        session_id: int,
        message_id: int,
        question: str,
        answer: str,
        citations: List[dict],
    ) -> None:
        """采集检索、回答、延迟指标。"""
        try:
            # 检索指标
            retrieved_docs = result.get("retrieved_docs") or []
            top_scores = [
                float(d.get("similarity_score") or d.get("score") or 0.0)
                for d in retrieved_docs
                if isinstance(d, dict)
            ][:5]
            retrieval_latency = int(result.get("retrieval_latency_ms", 0) or 0)
            await recall_metrics.record_retrieval(
                db,
                question_log_id=None,
                retrieved_count=len(retrieved_docs),
                top_scores=top_scores,
                latency_ms=retrieval_latency,
                session_id=session_id,
            )
        except Exception as exc:
            logger.warning(f"采集检索指标失败: {exc}")

        try:
            # 回答指标
            await answer_metrics.record_answer(
                db,
                message_id=message_id,
                citation_count=len(citations),
                answer_length=len(answer),
                hallucination_flag=bool(result.get("has_hallucination", False)),
                rejection_flag=bool(result.get("should_reject", False)),
                retry_count=int(result.get("retry_count", 0) or 0),
                session_id=session_id,
            )
        except Exception as exc:
            logger.warning(f"采集回答指标失败: {exc}")

        try:
            # 延迟指标（非流式场景记录 e2e，流式场景由调用方单独记录）
            agent_start = float(result.get("agent_start_time", 0) or 0)
            if agent_start > 0:
                import time as _time
                e2e_ms = int((_time.time() - agent_start) * 1000)
                await latency_metrics.record_e2e_latency(
                    db,
                    session_id=session_id,
                    message_id=message_id,
                    e2e_ms=e2e_ms,
                    retrieval_ms=int(result.get("retrieval_latency_ms", 0) or 0),
                    generation_ms=int(result.get("generation_latency_ms", 0) or 0),
                )
        except Exception as exc:
            logger.warning(f"采集延迟指标失败: {exc}")

    @staticmethod
    def _sse(payload: dict) -> str:
        """构造一条 SSE 数据帧。"""
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


# 模块级单例
chat_service = ChatService()
