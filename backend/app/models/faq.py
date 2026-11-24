"""FAQ 与问题日志模型。"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FAQ(Base):
    """常见问题表。

    可由 LLM 自动生成并经人工审核后发布。
    """

    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # 来源文档信息（JSON 数组）
    source_documents: Mapped[Optional[Any]] = mapped_column(JSON, default=None)
    ask_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 状态: pending / published / rejected
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FAQ(id={self.id}, question={self.question[:30]}...)>"


class QuestionLog(Base):
    """问题日志表。

    记录用户提问用于意图分析与问答质量改进。
    """

    __tablename__ = "question_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    # 问题意图分类
    intent: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    # 是否为有效问题
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("chat_sessions.id", ondelete="SET NULL"), default=None
    )
    asked_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<QuestionLog(id={self.id}, question={self.question[:30]}...)>"
