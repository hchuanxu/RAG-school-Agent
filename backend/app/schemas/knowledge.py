"""知识库相关 Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求。"""

    name: str = Field(..., min_length=1, max_length=128, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    is_public: bool = Field(True, description="是否公开")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求。"""

    name: Optional[str] = Field(None, min_length=1, max_length=128, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    is_public: Optional[bool] = Field(None, description="是否公开")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应。"""

    id: int = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    is_public: bool = Field(..., description="是否公开")
    collection_name: str = Field(..., description="ChromaDB 集合名称")
    document_count: int = Field(0, description="文档数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}
