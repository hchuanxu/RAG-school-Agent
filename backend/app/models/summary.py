"""文档总结、关键规则与生成问题模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Summary(Base):
    """文档总结表。"""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, document_id={self.document_id})>"


class KeyRule(Base):
    """关键规则表。

    从文档中抽取的关键规则与要点。
    """

    __tablename__ = "key_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_location: Mapped[Optional[str]] = mapped_column(String(256), default=None)
    category: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    importance_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<KeyRule(id={self.id}, document_id={self.document_id}, title={self.title})>"


class GeneratedQuestion(Base):
    """生成问题表。

    基于文档由 LLM 自动生成的问答对，可用于学习与考核。
    """

    __tablename__ = "generated_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # 难度: easy / medium / hard
    difficulty: Mapped[Optional[str]] = mapped_column(String(16), default="medium")
    category: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    source_location: Mapped[Optional[str]] = mapped_column(String(256), default=None)

    def __repr__(self) -> str:
        return f"<GeneratedQuestion(id={self.id}, document_id={self.document_id})>"
