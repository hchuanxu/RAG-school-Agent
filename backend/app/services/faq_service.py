"""FAQ 智能生成服务。

基于 QuestionLog 的高频问题，结合 RAG 检索与 LLM 生成标准答案，
经人工审核后发布到 ChromaDB，为问答系统提供快速回答能力。
"""
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, ResourceNotFoundError
from app.core.llm_factory import create_chat_llm
from app.models.faq import FAQ, QuestionLog
from app.models.knowledge_base import KnowledgeBase
from app.rag.embeddings.embedding_factory import EmbeddingFactory
from app.rag.prompts.chat_prompts import ANSWER_GENERATION_PROMPT, SYSTEM_PROMPT
from app.rag.retrievers.hybrid_retriever import HybridRetriever
from app.rag.vectorstore.chroma_manager import ChromaManager
from app.schemas.common import PaginatedResponse


# FAQ 专用 ChromaDB 集合名
FAQ_COLLECTION_NAME = "faqs"


class FAQService:
    """FAQ 智能生成服务。"""

    def __init__(self) -> None:
        self.chroma_manager = ChromaManager()
        self.embedding_factory = EmbeddingFactory()
        self.retriever = HybridRetriever(
            embedding_factory=self.embedding_factory,
            chroma_manager=self.chroma_manager,
        )
        # 确保集合存在
        self.chroma_manager.create_collection(FAQ_COLLECTION_NAME)

    # ------------------------------------------------------------------ #
    # FAQ 自动生成
    # ------------------------------------------------------------------ #
    async def generate_faq(
        self, db: AsyncSession, threshold: int = 10
    ) -> Dict[str, Any]:
        """基于高频问题自动生成 FAQ。

        Args:
            db: 异步数据库会话。
            threshold: 触发生成的最低提问次数，默认 10。

        Returns:
            ``{generated_count, skipped_count, faqs: [...]}``。
        """
        threshold = max(1, int(threshold or 10))

        # 聚合高频问题（仅统计有效问题）
        stmt = (
            select(
                QuestionLog.question,
                func.count(QuestionLog.id).label("count"),
            )
            .where(QuestionLog.is_valid.is_(True))
            .group_by(QuestionLog.question)
            .having(func.count(QuestionLog.id) >= threshold)
            .order_by(func.count(QuestionLog.id).desc())
        )
        result = await db.execute(stmt)
        hot_questions = result.all()

        if not hot_questions:
            logger.info(f"未找到提问次数 >= {threshold} 的高频问题")
            return {"generated_count": 0, "skipped_count": 0, "faqs": []}

        # 查询已有的 pending/published FAQ 问题集合，避免重复生成
        existing_stmt = select(FAQ.question).where(
            FAQ.status.in_(["pending", "published"])
        )
        existing_result = await db.execute(existing_stmt)
        existing_questions = {row[0] for row in existing_result.all()}

        # 获取所有知识库集合名
        kb_stmt = select(KnowledgeBase.collection_name)
        kb_result = await db.execute(kb_stmt)
        collection_names = [row[0] for row in kb_result.all()]

        generated_faqs: List[Dict[str, Any]] = []
        skipped_count = 0

        for row in hot_questions:
            question_text = row[0]
            ask_count = int(row[1] or 0)
            if question_text in existing_questions:
                skipped_count += 1
                continue

            try:
                answer, source_documents = await self._generate_answer(
                    question_text, collection_names
                )
                if not answer:
                    skipped_count += 1
                    continue

                faq = FAQ(
                    question=question_text[:512],
                    answer=answer,
                    source_documents=source_documents or None,
                    ask_count=ask_count,
                    status="pending",
                    auto_generated=True,
                )
                db.add(faq)
                await db.commit()
                await db.refresh(faq)

                generated_faqs.append(
                    {
                        "id": faq.id,
                        "question": faq.question,
                        "answer": faq.answer,
                        "ask_count": faq.ask_count,
                        "source_documents": faq.source_documents,
                        "status": faq.status,
                    }
                )
                logger.info(
                    f"FAQ 已生成: id={faq.id}, ask_count={ask_count}, "
                    f"question={question_text[:30]}"
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    f"FAQ 生成失败: question={question_text[:30]}, error={exc}"
                )
                skipped_count += 1
                continue

        logger.info(
            f"FAQ 批量生成完成: generated={len(generated_faqs)}, skipped={skipped_count}"
        )
        return {
            "generated_count": len(generated_faqs),
            "skipped_count": skipped_count,
            "faqs": generated_faqs,
        }

    # ------------------------------------------------------------------ #
    # 查询接口
    # ------------------------------------------------------------------ #
    async def get_faq_list(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[Dict[str, Any]]:
        """分页获取 FAQ 列表。

        Args:
            db: 异步数据库会话。
            status: 状态筛选，pending/published/rejected，None 表示全部。
            page: 页码，从 1 开始。
            page_size: 每页条数。
        """
        page = max(1, int(page or 1))
        page_size = max(1, min(int(page_size or 20), 100))

        total_stmt = select(func.count(FAQ.id))
        if status:
            total_stmt = total_stmt.where(FAQ.status == status)
        total = int((await db.execute(total_stmt)).scalar_one() or 0)

        stmt = (
            select(FAQ)
            .order_by(FAQ.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        if status:
            stmt = stmt.where(FAQ.status == status)
        result = await db.execute(stmt)
        faqs = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total else 0
        return PaginatedResponse[Dict[str, Any]](
            items=[self._to_dict(f) for f in faqs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_faq(self, db: AsyncSession, faq_id: int) -> Dict[str, Any]:
        """获取 FAQ 详情。"""
        faq = await self._get_faq_or_404(db, faq_id)
        return self._to_dict(faq)

    # ------------------------------------------------------------------ #
    # 审核与维护
    # ------------------------------------------------------------------ #
    async def publish_faq(
        self, db: AsyncSession, faq_id: int, reviewer_id: int
    ) -> Dict[str, Any]:
        """发布 FAQ：更新状态并写入 ChromaDB。

        Args:
            db: 异步数据库会话。
            faq_id: FAQ ID。
            reviewer_id: 审核人用户 ID。
        """
        faq = await self._get_faq_or_404(db, faq_id)
        if faq.status == "published":
            raise BusinessException("FAQ 已发布，无需重复操作")

        # 写入 ChromaDB
        try:
            metadata = {
                "faq_id": str(faq.id),
                "question": faq.question,
                "source_documents": (
                    ",".join(faq.source_documents)
                    if isinstance(faq.source_documents, list)
                    else str(faq.source_documents or "")
                ),
                "type": "faq",
            }
            # 优先使用 EmbeddingFactory 生成向量
            embeddings = None
            try:
                embedder = self.embedding_factory.get_embedder()
                embeddings = embedder.embed_documents([faq.answer])
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"FAQ 向量化失败，回退至 ChromaDB 默认嵌入: {exc}")
                embeddings = None

            self.chroma_manager.add_documents(
                collection_name=FAQ_COLLECTION_NAME,
                texts=[faq.answer],
                metadatas=[metadata],
                ids=[f"faq_{faq.id}"],
                embeddings=embeddings,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"FAQ 写入 ChromaDB 失败: id={faq_id}, error={exc}")
            raise BusinessException(f"FAQ 发布失败（写入向量库异常）: {exc}")

        faq.status = "published"
        faq.reviewed_by = reviewer_id
        await db.commit()
        await db.refresh(faq)
        logger.info(f"FAQ 已发布: id={faq_id}, reviewer={reviewer_id}")
        return self._to_dict(faq)

    async def reject_faq(
        self, db: AsyncSession, faq_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """拒绝 FAQ。"""
        faq = await self._get_faq_or_404(db, faq_id)
        if faq.status == "rejected":
            raise BusinessException("FAQ 已拒绝，无需重复操作")
        if faq.status == "published":
            # 已发布的 FAQ 拒绝时需从 ChromaDB 移除
            try:
                self.chroma_manager.delete_by_metadata(
                    collection_name=FAQ_COLLECTION_NAME,
                    metadata_key="faq_id",
                    metadata_value=str(faq_id),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"从 ChromaDB 移除已拒绝 FAQ 失败: id={faq_id}, error={exc}"
                )

        faq.status = "rejected"
        await db.commit()
        await db.refresh(faq)
        logger.info(f"FAQ 已拒绝: id={faq_id}, reason={reason}")
        return self._to_dict(faq)

    async def update_faq(
        self, db: AsyncSession, faq_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 FAQ 内容（仅 question / answer / source_documents 可更新）。"""
        faq = await self._get_faq_or_404(db, faq_id)
        allowed_fields = {"question", "answer", "source_documents"}
        for field in allowed_fields:
            if field in data:
                value = data[field]
                if field == "question":
                    value = str(value)[:512] if value else faq.question
                setattr(faq, field, value)

        # 若 FAQ 已发布且 answer 被更新，同步更新 ChromaDB
        if faq.status == "published" and "answer" in data:
            try:
                self.chroma_manager.delete_by_metadata(
                    collection_name=FAQ_COLLECTION_NAME,
                    metadata_key="faq_id",
                    metadata_value=str(faq_id),
                )
                metadata = {
                    "faq_id": str(faq.id),
                    "question": faq.question,
                    "type": "faq",
                }
                embeddings = None
                try:
                    embedder = self.embedding_factory.get_embedder()
                    embeddings = embedder.embed_documents([faq.answer])
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"FAQ 更新向量化失败: {exc}")
                self.chroma_manager.add_documents(
                    collection_name=FAQ_COLLECTION_NAME,
                    texts=[faq.answer],
                    metadatas=[metadata],
                    ids=[f"faq_{faq.id}"],
                    embeddings=embeddings,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"更新已发布 FAQ 向量失败: id={faq_id}, error={exc}")

        await db.commit()
        await db.refresh(faq)
        logger.info(f"FAQ 已更新: id={faq_id}")
        return self._to_dict(faq)

    async def delete_faq(self, db: AsyncSession, faq_id: int) -> None:
        """删除 FAQ：同时从 ChromaDB 移除。"""
        faq = await self._get_faq_or_404(db, faq_id)
        # 从 ChromaDB 移除（若已发布）
        try:
            self.chroma_manager.delete_by_metadata(
                collection_name=FAQ_COLLECTION_NAME,
                metadata_key="faq_id",
                metadata_value=str(faq_id),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"删除 FAQ 向量失败: id={faq_id}, error={exc}")

        await db.delete(faq)
        await db.commit()
        logger.info(f"FAQ 已删除: id={faq_id}")

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    async def _get_faq_or_404(self, db: AsyncSession, faq_id: int) -> FAQ:
        result = await db.execute(select(FAQ).where(FAQ.id == faq_id))
        faq = result.scalar_one_or_none()
        if faq is None:
            raise ResourceNotFoundError("FAQ 不存在")
        return faq

    async def _generate_answer(
        self, question: str, collection_names: List[str]
    ) -> tuple[str, List[str]]:
        """通过 RAG 检索 + LLM 生成 FAQ 标准答案。

        Args:
            question: 用户问题。
            collection_names: 待检索的知识库集合名列表。

        Returns:
            (答案文本, 来源文档名列表)。
        """
        if not collection_names:
            logger.warning("无可用的知识库集合，无法生成 FAQ 答案")
            return "", []

        # 同步检索：HybridRetriever.retrieve 是同步方法，使用 to_thread 包装
        import asyncio

        try:
            docs = await asyncio.to_thread(
                self.retriever.retrieve,
                question,
                collection_names,
                5,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"FAQ 生成检索失败: question={question[:30]}, error={exc}")
            return "", []

        if not docs:
            logger.info(f"FAQ 生成无相关检索结果: question={question[:30]}")
            return "", []

        # 构建上下文
        context_parts: List[str] = []
        source_documents: List[str] = []
        for idx, doc in enumerate(docs, start=1):
            content = (doc.get("content") or "").strip()
            file_name = doc.get("file_name") or "未知文档"
            page = doc.get("page")
            page_info = f"，第{page}页" if page is not None else ""
            context_parts.append(f"[来源{idx}] {file_name}{page_info}\n{content}")
            if file_name not in source_documents:
                source_documents.append(file_name)
        context = "\n\n".join(context_parts)

        # 调用 LLM 生成答案
        try:
            llm = create_chat_llm()
            prompt = ANSWER_GENERATION_PROMPT.format(
                question=question, context=context
            )
            full_prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"请基于检索资料为以下问题生成一条简洁、规范的 FAQ 标准答案，"
                f"适合作为常见问题解答展示给用户。\n\n"
                f"{prompt}"
            )
            response = await llm.ainvoke(full_prompt)
            answer = (
                response.content if hasattr(response, "content") else str(response)
            )
            answer = (answer or "").strip()
            logger.info(
                f"FAQ 答案生成完成: question={question[:30]}, "
                f"answer_len={len(answer)}, sources={len(source_documents)}"
            )
            return answer, source_documents
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"FAQ 答案生成失败: question={question[:30]}, error={exc}")
            return "", []

    @staticmethod
    def _to_dict(faq: FAQ) -> Dict[str, Any]:
        """将 FAQ 对象转为字典。"""
        return {
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "source_documents": faq.source_documents,
            "ask_count": faq.ask_count,
            "status": faq.status,
            "auto_generated": faq.auto_generated,
            "reviewed_by": faq.reviewed_by,
            "created_at": faq.created_at.isoformat() if faq.created_at else None,
            "updated_at": faq.updated_at.isoformat() if faq.updated_at else None,
        }


# 模块级单例
faq_service = FAQService()
