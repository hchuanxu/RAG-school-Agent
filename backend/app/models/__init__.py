"""数据模型集合。

导入所有 ORM 模型，便于 Alembic 迁移与统一注册。
"""
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.models.faq import FAQ, QuestionLog
from app.models.knowledge_base import KnowledgeBase
from app.models.metrics import AnswerMetrics, LatencyMetrics, RetrievalMetrics, UserFeedback
from app.models.summary import GeneratedQuestion, KeyRule, Summary
from app.models.user import User

__all__ = [
    "User",
    "KnowledgeBase",
    "Document",
    "ChatSession",
    "ChatMessage",
    "FAQ",
    "QuestionLog",
    "Summary",
    "KeyRule",
    "GeneratedQuestion",
    "RetrievalMetrics",
    "AnswerMetrics",
    "LatencyMetrics",
    "UserFeedback",
]
