"""评价指标模型。"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RetrievalMetrics(Base):
    """检索质量指标表。

    记录单次问答的召回情况，用于评估检索效果。
    """

    __tablename__ = "retrieval_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_log_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("question_logs.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    # 召回文档切片数
    retrieved_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 命中标注数，初始 NULL
    hit_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    # 首位命中排名
    first_relevant_rank: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    # Top-K 检索得分列表
    top_scores: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, default=None)
    # 检索耗时毫秒
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<RetrievalMetrics(id={self.id}, "
            f"retrieved_count={self.retrieved_count}, hit_count={self.hit_count})>"
        )


class AnswerMetrics(Base):
    """回答质量指标表。

    记录回答的引用、长度与幻觉等质量信息。
    """

    __tablename__ = "answer_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    session_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    # 引用数量
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 引用准确率，0-1
    citation_accuracy: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )
    # 回答字符数
    answer_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 幻觉标记
    hallucination_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # 拒绝回答标记
    rejection_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # 重试次数
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<AnswerMetrics(id={self.id}, message_id={self.message_id}, "
            f"citation_count={self.citation_count})>"
        )


class LatencyMetrics(Base):
    """性能延迟指标表。

    记录问答各阶段的耗时，用于性能分析。
    """

    __tablename__ = "latency_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    # 首字延迟毫秒
    ttft_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    # 端到端延迟毫秒
    e2e_latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    # 检索耗时
    retrieval_latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    # 生成耗时
    generation_latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<LatencyMetrics(id={self.id}, message_id={self.message_id}, "
            f"e2e_latency_ms={self.e2e_latency_ms})>"
        )


class UserFeedback(Base):
    """用户反馈表。

    记录用户对回答的点赞/点踩、评分与文字反馈。
    """

    __tablename__ = "user_feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "message_id", name="uq_user_message_feedback"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # 反馈类型: upvote / downvote
    feedback_type: Mapped[str] = mapped_column(String(16), nullable=False)
    # 1-5 星评分
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
    # 文字反馈
    feedback_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<UserFeedback(id={self.id}, user_id={self.user_id}, "
            f"message_id={self.message_id}, feedback_type={self.feedback_type})>"
        )
