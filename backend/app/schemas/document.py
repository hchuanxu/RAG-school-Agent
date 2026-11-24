"""文档相关 Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """文档响应。"""

    id: int = Field(..., description="文档ID")
    knowledge_base_id: int = Field(..., description="所属知识库ID")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件存储路径")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    status: str = Field(..., description="处理状态：processing/completed/failed")
    chunk_count: int = Field(..., description="分块数量")
    uploaded_at: datetime = Field(..., description="上传时间")
    summary_status: str = Field(..., description="总结状态：pending/processing/completed/failed")

    model_config = {"from_attributes": True}


class DocumentSummaryResponse(BaseModel):
    """文档总结响应。"""

    document_id: int = Field(..., description="文档ID")
    summary_text: str = Field(..., description="总结内容")
    created_at: datetime = Field(..., description="总结生成时间")

    model_config = {"from_attributes": True}


class DocumentUploadAck(BaseModel):
    """文档上传确认。"""

    document_id: int = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    status: str = Field(..., description="初始处理状态")
