"""通用 Schema：统一响应与分页响应。"""
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """统一响应结构。"""

    code: int = Field(200, description="业务状态码，200 表示成功")
    message: str = Field("success", description="提示信息")
    data: Optional[T] = Field(None, description="响应数据")

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应结构。"""

    items: List[T] = Field(default_factory=list, description="当前页数据列表")
    total: int = Field(0, description="数据总条数")
    page: int = Field(1, description="当前页码，从 1 开始")
    page_size: int = Field(20, description="每页条数")
    total_pages: int = Field(0, description="总页数")

    model_config = {"from_attributes": True}
