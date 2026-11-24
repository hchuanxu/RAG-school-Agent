"""对话相关 Schema。"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse


class ChatRequest(BaseModel):
    """对话请求。"""

    question: str = Field(..., min_length=1, description="用户问题")
    session_id: Optional[int] = Field(None, description="会话ID，为空则新建会话")
    knowledge_base_ids: Optional[List[int]] = Field(
        None, description="知识库ID列表，为空则使用全部公开知识库"
    )


class ChatMessageResponse(BaseModel):
    """对话消息响应。"""

    role: str = Field(..., description="消息角色：user/assistant")
    content: str = Field(..., description="消息内容")
    citations: Optional[Any] = Field(None, description="引用溯源信息")
    created_at: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


class ChatSessionResponse(BaseModel):
    """对话会话响应。"""

    id: int = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    message_count: int = Field(0, description="消息数量")

    model_config = {"from_attributes": True}


class ChatHistoryResponse(PaginatedResponse[ChatMessageResponse]):
    """对话历史分页响应。"""

    pass


class SessionRenameRequest(BaseModel):
    """会话重命名请求。"""

    title: str = Field(..., min_length=1, max_length=256, description="新标题")
