"""溯源（引用）相关 Schema。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CitationResponse(BaseModel):
    """引用溯源响应。

    用于在对话回复中标注信息来源，支持文档、页码、段落、分块等多级定位。
    """

    citation_id: str = Field(..., description="引用唯一标识")
    document_id: int = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    knowledge_base_name: str = Field(..., description="所属知识库名称")
    page: Optional[int] = Field(None, description="页码（PDF 等）")
    paragraph: Optional[str] = Field(None, description="段落定位")
    chunk_index: Optional[int] = Field(None, description="分块索引")
    content_preview: str = Field(..., description="内容预览（截断）")
    full_content: Optional[str] = Field(None, description="完整内容")
    similarity_score: Optional[float] = Field(None, description="相似度得分（0~1）")
    uploaded_at: datetime = Field(..., description="文档上传时间")

    model_config = {"from_attributes": True}
