"""知识库服务。

管理知识库元数据与 ChromaDB 集合的创建、查询、更新、删除及统计。
"""
import re
from uuid import uuid4

from loguru import logger
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, ResourceNotFoundError
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.rag.vectorstore.chroma_manager import ChromaManager
from app.schemas.common import PaginatedResponse
from app.schemas.knowledge import (
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)


class KnowledgeService:
    """知识库服务。"""

    def __init__(self) -> None:
        self.chroma_manager = ChromaManager()

    def _generate_collection_name(self, name: str) -> str:
        """生成 ChromaDB 集合名。

        ChromaDB 集合名仅允许小写字母、数字、下划线/连字符，长度 3-63，
        因此将非 ASCII 字母数字字符替换为下划线，并附加随机后缀保证唯一。
        """
        safe = re.sub(r"[^a-zA-Z0-9]+", "_", name or "").strip("_").lower()
        if not safe:
            safe = "kb"
        suffix = uuid4().hex[:8]
        return f"kb_{safe}_{suffix}"

    async def create_knowledge_base(
        self,
        db: AsyncSession,
        name: str,
        description: str | None = None,
        is_public: bool = True,
    ) -> KnowledgeBaseResponse:
        """创建知识库并在 ChromaDB 创建对应集合。

        Raises:
            BusinessException: 知识库名称已存在。
        """
        existing = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )
        if existing.scalar_one_or_none() is not None:
            raise BusinessException(code=409, message="知识库名称已存在")

        collection_name = self._generate_collection_name(name)
        # 在 ChromaDB 中创建集合
        self.chroma_manager.create_collection(collection_name)
        logger.info(f"ChromaDB 集合已创建: {collection_name}")

        kb = KnowledgeBase(
            name=name,
            description=description,
            is_public=is_public,
            collection_name=collection_name,
        )
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
        logger.info(f"知识库已创建: id={kb.id}, name={kb.name}")
        return KnowledgeBaseResponse.model_validate(kb)

    async def get_knowledge_base(
        self, db: AsyncSession, kb_id: int
    ) -> KnowledgeBase:
        """获取知识库，不存在则抛出 404。"""
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        if kb is None:
            raise ResourceNotFoundError("知识库不存在")
        return kb

    async def list_knowledge_bases(
        self, db: AsyncSession, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[KnowledgeBaseResponse]:
        """分页获取知识库列表（含文档数量）。"""
        page = max(page, 1)
        page_size = max(min(page_size, 100), 1)

        total_result = await db.execute(select(func.count(KnowledgeBase.id)))
        total = total_result.scalar_one()

        # 关联查询文档数量
        result = await db.execute(
            select(
                KnowledgeBase,
                func.count(Document.id).label("document_count"),
            )
            .outerjoin(Document, Document.knowledge_base_id == KnowledgeBase.id)
            .group_by(KnowledgeBase.id)
            .order_by(KnowledgeBase.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = result.all()

        total_pages = (total + page_size - 1) // page_size if total else 0
        items = []
        for kb, doc_count in rows:
            item = KnowledgeBaseResponse.model_validate(kb)
            item.document_count = int(doc_count or 0)
            items.append(item)
        return PaginatedResponse[KnowledgeBaseResponse](
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update_knowledge_base(
        self, db: AsyncSession, kb_id: int, data: KnowledgeBaseUpdate
    ) -> KnowledgeBaseResponse:
        """更新知识库信息。"""
        kb = await self.get_knowledge_base(db, kb_id)

        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] is not None:
            existing = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.name == update_data["name"],
                    KnowledgeBase.id != kb_id,
                )
            )
            if existing.scalar_one_or_none() is not None:
                raise BusinessException(code=409, message="知识库名称已存在")
        for field, value in update_data.items():
            setattr(kb, field, value)

        await db.commit()
        await db.refresh(kb)
        logger.info(f"知识库已更新: id={kb_id}")
        return KnowledgeBaseResponse.model_validate(kb)

    async def delete_knowledge_base(
        self, db: AsyncSession, kb_id: int
    ) -> None:
        """删除知识库：先删除 ChromaDB 集合，再删除数据库记录。"""
        kb = await self.get_knowledge_base(db, kb_id)

        # 删除 ChromaDB 集合
        self.chroma_manager.delete_collection(kb.collection_name)
        # 删除数据库记录（级联删除关联文档）
        await db.delete(kb)
        await db.commit()
        logger.info(f"知识库已删除: id={kb_id}, collection={kb.collection_name}")

    async def get_knowledge_base_stats(
        self, db: AsyncSession, kb_id: int
    ) -> dict:
        """获取知识库统计信息。"""
        kb = await self.get_knowledge_base(db, kb_id)

        doc_result = await db.execute(
            select(
                func.count(Document.id),
                func.sum(
                    case(
                        (Document.status == "completed", 1), else_=0
                    )
                ),
                func.sum(Document.chunk_count),
            ).where(Document.knowledge_base_id == kb_id)
        )
        total_docs, completed_docs, total_chunks = doc_result.one()

        chroma_stats = self.chroma_manager.get_collection_stats(
            kb.collection_name
        )
        return {
            "knowledge_base_id": kb.id,
            "name": kb.name,
            "document_count": int(total_docs or 0),
            "completed_documents": int(completed_docs or 0),
            "processing_documents": int((total_docs or 0) - (completed_docs or 0)),
            "total_chunks": int(total_chunks or 0),
            "vector_count": chroma_stats.get("count", 0),
        }


# 模块级单例
knowledge_service = KnowledgeService()
