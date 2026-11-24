"""溯源（引用）服务。

根据引用唯一标识（``{message_id}:{index}``）解析并返回引用详情，
结合数据库补全文档与知识库元信息。
"""
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError
from app.models.chat import ChatMessage
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.schemas.citation import CitationResponse


class CitationService:
    """溯源服务。"""

    async def get_citation(
        self, db: AsyncSession, citation_id: str
    ) -> CitationResponse:
        """根据 citation_id 获取引用详情。

        Args:
            db: 异步数据库会话。
            citation_id: 引用唯一标识，格式为 ``{message_id}:{index}``。

        Returns:
            引用溯源响应。

        Raises:
            ResourceNotFoundError: 标识非法或引用不存在。
        """
        message_id, index = self._parse_citation_id(citation_id)

        # 加载消息
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        if message is None:
            raise ResourceNotFoundError("引用所属消息不存在")

        citations = message.citations or []
        if not isinstance(citations, list) or index >= len(citations):
            raise ResourceNotFoundError("引用不存在或索引越界")

        citation = citations[index] or {}

        file_name = citation.get("file_name", "")
        collection_name = citation.get("knowledge_base", "")

        # 补全知识库与文档信息
        knowledge_base_name = collection_name
        document_id = 0
        uploaded_at = message.created_at

        if collection_name:
            kb_result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.collection_name == collection_name
                )
            )
            kb = kb_result.scalar_one_or_none()
            if kb is not None:
                knowledge_base_name = kb.name
                if file_name:
                    doc_result = await db.execute(
                        select(Document).where(
                            Document.knowledge_base_id == kb.id,
                            Document.filename == file_name,
                        )
                    )
                    doc = doc_result.scalars().first()
                    if doc is not None:
                        document_id = doc.id
                        uploaded_at = doc.uploaded_at

        preview = citation.get("content_preview", "")

        return CitationResponse(
            citation_id=citation_id,
            document_id=document_id,
            filename=file_name,
            knowledge_base_name=knowledge_base_name,
            page=citation.get("page"),
            paragraph=(
                str(citation.get("paragraph"))
                if citation.get("paragraph") is not None
                else None
            ),
            chunk_index=citation.get("chunk_index"),
            content_preview=preview,
            full_content=preview or None,
            similarity_score=citation.get("similarity_score"),
            uploaded_at=uploaded_at,
        )

    @staticmethod
    def _parse_citation_id(citation_id: str) -> tuple:
        """解析 citation_id 为 (message_id, index)。"""
        try:
            parts = citation_id.split(":")
            if len(parts) != 2:
                raise ValueError("格式非法")
            message_id = int(parts[0])
            index = int(parts[1])
            if message_id < 0 or index < 0:
                raise ValueError("非法值")
            return message_id, index
        except (ValueError, TypeError) as exc:
            raise ResourceNotFoundError(f"引用标识非法: {citation_id}") from exc


# 模块级单例
citation_service = CitationService()
