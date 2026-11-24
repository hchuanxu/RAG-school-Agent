"""智能体状态定义。

定义 LangGraph 工作流中使用的意图类别、引用溯源结构与全局状态。
"""
from typing import Any, List, Optional, TypedDict
from enum import Enum


class IntentType(str, Enum):
    """意图类别枚举。"""

    CAMPUS_POLICY = "campus_policy"
    ACADEMIC_AFFAIRS = "academic_affairs"
    SCHOLARSHIP = "scholarship"
    CAMPUS_LIFE = "campus_life"
    CASUAL_CHAT = "casual_chat"
    INVALID = "invalid"
    OUT_OF_SCOPE = "out_of_scope"


class Citation(TypedDict):
    """引用溯源信息。"""

    file_name: str
    page: Optional[int]
    paragraph: Optional[int]
    chunk_index: int
    knowledge_base: str
    content_preview: str
    similarity_score: float


class AgentState(TypedDict):
    """LangGraph 工作流状态。"""

    messages: List[dict]  # 对话历史
    conversation_id: str
    question: str  # 当前问题
    intent: str
    intent_confidence: float
    retrieved_docs: List[dict]
    no_relevant_docs: bool
    citations: List[Citation]
    answer: str
    review_passed: bool
    has_hallucination: bool
    has_sensitive_content: bool
    review_suggestions: str
    final_answer: str
    should_reject: bool
    reject_reason: str
    knowledge_base_ids: List[str]
    retry_count: int  # 审核未通过时的重试计数
    # 指标采集相关（同步节点记录，异步服务消费）
    retrieval_latency_ms: int
    generation_latency_ms: int
    agent_start_time: float
