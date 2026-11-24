"""统计路由。

- GET /dashboard 全局统计概览
- GET /usage     当前用户使用情况
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_current_user
from app.db.session import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.models.faq import QuestionLog
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User

router = APIRouter(prefix="/stats", tags=["统计"])


async def _count(db: AsyncSession, model) -> int:
    result = await db.execute(select(func.count(model.id)))
    return int(result.scalar_one())


@router.get("/dashboard", summary="全局统计概览")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict:
    """返回用户、知识库、文档、会话、消息等全局计数。

    响应键名与前端 DashboardStats 类型对齐：
    total_questions / total_knowledge_bases / total_users / today_questions
    """
    doc_status_result = await db.execute(
        select(Document.status, func.count(Document.id)).group_by(Document.status)
    )
    doc_status = {row[0]: int(row[1]) for row in doc_status_result.all()}

    # 今日提问数：QuestionLog.asked_at >= 当天零点
    today_start = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    today_q_result = await db.execute(
        select(func.count(QuestionLog.id)).where(
            QuestionLog.asked_at >= today_start
        )
    )
    today_questions = int(today_q_result.scalar_one() or 0)

    total_sessions = await _count(db, ChatSession)
    total_users = await _count(db, User)
    total_kbs = await _count(db, KnowledgeBase)

    return {
        # —— 前端 DashboardStats 期望的键 ——
        "total_questions": total_sessions,
        "total_knowledge_bases": total_kbs,
        "total_users": total_users,
        "today_questions": today_questions,
        "questions_change": None,
        "users_change": None,
        # —— 兼容旧消费者的额外键 ——
        "users": total_users,
        "knowledge_bases": total_kbs,
        "documents": await _count(db, Document),
        "documents_completed": doc_status.get("completed", 0),
        "documents_processing": doc_status.get("processing", 0),
        "documents_failed": doc_status.get("failed", 0),
        "chat_sessions": total_sessions,
        "chat_messages": await _count(db, ChatMessage),
        "question_logs": await _count(db, QuestionLog),
    }


@router.get("/usage", summary="当前用户使用情况")
async def usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """返回当前用户的会话与消息计数。"""
    session_count_result = await db.execute(
        select(func.count(ChatSession.id)).where(
            ChatSession.user_id == current_user.id
        )
    )
    message_count_result = await db.execute(
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == current_user.id)
    )
    question_count_result = await db.execute(
        select(func.count(QuestionLog.id)).where(
            QuestionLog.user_id == current_user.id
        )
    )
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "chat_sessions": int(session_count_result.scalar_one()),
        "chat_messages": int(message_count_result.scalar_one()),
        "questions_asked": int(question_count_result.scalar_one()),
    }
