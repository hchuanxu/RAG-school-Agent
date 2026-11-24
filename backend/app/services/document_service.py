"""文档服务。

负责文档上传、解析、清洗、切片、向量化与入库，以及文档的查询、
删除与重建索引等操作。
"""
import asyncio
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import aiofiles
from fastapi import UploadFile
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BusinessException, FileProcessingError, ResourceNotFoundError
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.rag.embeddings.embedding_factory import EmbeddingFactory
from app.rag.processors.docx_processor import DOCXProcessor
from app.rag.processors.document_splitter import DocumentSplitter
from app.rag.processors.pdf_processor import PDFProcessor
from app.rag.processors.text_cleaner import TextCleaner
from app.rag.processors.txt_processor import TXTProcessor
from app.rag.vectorstore.chroma_manager import ChromaManager
from app.schemas.common import PaginatedResponse
from app.schemas.document import DocumentResponse, DocumentUploadAck
from app.services.knowledge_service import knowledge_service

# 文件扩展名到处理器类型的映射
_EXT_TO_TYPE = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "txt",
}


class DocumentService:
    """文档服务。"""

    def __init__(self) -> None:
        self.chroma_manager = ChromaManager()
        self.embedding_factory = EmbeddingFactory()
        self.text_cleaner = TextCleaner()
        self.splitter = DocumentSplitter()
        self.pdf_processor = PDFProcessor()
        self.docx_processor = DOCXProcessor()
        self.txt_processor = TXTProcessor()

    # ------------------------------------------------------------------ #
    # 上传与处理
    # ------------------------------------------------------------------ #
    async def upload_document(
        self, db: AsyncSession, kb_id: int, file: UploadFile
    ) -> DocumentUploadAck:
        """上传文档并触发解析、向量化与入库。"""
        # 校验知识库存在
        kb = await knowledge_service.get_knowledge_base(db, kb_id)

        # 校验文件类型
        original_name = file.filename or "untitled"
        ext = Path(original_name).suffix.lower()
        if ext not in _EXT_TO_TYPE:
            raise BusinessException(
                code=400, message=f"不支持的文件类型: {ext}（支持 pdf/docx/txt/md）"
            )
        file_type = _EXT_TO_TYPE[ext]

        # 读取并校验文件大小
        content = await file.read()
        if not content:
            raise BusinessException(code=400, message="文件内容为空")
        if len(content) > settings.MAX_FILE_SIZE:
            raise BusinessException(
                code=413,
                message=f"文件过大，最大支持 {settings.MAX_FILE_SIZE // 1024 // 1024}MB",
            )

        # 保存文件到磁盘
        upload_dir = Path(settings.UPLOAD_DIR) / str(kb_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_name = f"{uuid4().hex}_{original_name}"
        file_path = upload_dir / saved_name
        async with aiofiles.open(str(file_path), "wb") as f:
            await f.write(content)

        # 创建数据库记录（初始状态 processing）
        document = Document(
            knowledge_base_id=kb_id,
            filename=original_name,
            file_path=str(file_path),
            file_size=len(content),
            file_type=file_type,
            status="processing",
            chunk_count=0,
            summary_status="pending",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        logger.info(
            f"文档已上传: id={document.id}, kb_id={kb_id}, filename={original_name}"
        )

        # 异步触发文档解析、向量化与入库（不阻塞 HTTP 请求）
        self._trigger_processing_async(
            doc_id=document.id,
            file_path=str(file_path),
            file_type=file_type,
            collection_name=kb.collection_name,
            filename=original_name,
            kb_id=kb_id,
        )

        return DocumentUploadAck(
            document_id=document.id,
            filename=document.filename,
            status=document.status,
        )

    async def get_document(
        self, db: AsyncSession, doc_id: int
    ) -> DocumentResponse:
        """获取文档详情。"""
        document = await self._get_document_or_404(db, doc_id)
        return DocumentResponse.model_validate(document)

    async def list_documents(
        self,
        db: AsyncSession,
        kb_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[DocumentResponse]:
        """分页获取指定知识库下的文档列表。"""
        page = max(page, 1)
        page_size = max(min(page_size, 100), 1)

        total_result = await db.execute(
            select(func.count(Document.id)).where(
                Document.knowledge_base_id == kb_id
            )
        )
        total = total_result.scalar_one()

        result = await db.execute(
            select(Document)
            .where(Document.knowledge_base_id == kb_id)
            .order_by(Document.uploaded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        docs = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total else 0
        return PaginatedResponse[DocumentResponse](
            items=[DocumentResponse.model_validate(d) for d in docs],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def delete_document(
        self, db: AsyncSession, doc_id: int
    ) -> None:
        """删除文档：删除向量、磁盘文件与数据库记录。"""
        document = await self._get_document_or_404(db, doc_id)

        # 查询所属知识库以获取集合名
        kb_result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == document.knowledge_base_id
            )
        )
        kb = kb_result.scalar_one_or_none()
        if kb is not None:
            self.chroma_manager.delete_by_metadata(
                collection_name=kb.collection_name,
                metadata_key="document_id",
                metadata_value=str(doc_id),
            )

        # 删除磁盘文件
        file_path = Path(document.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError as exc:
                logger.warning(f"删除文件失败: {file_path} - {exc}")

        await db.delete(document)
        await db.commit()
        logger.info(f"文档已删除: id={doc_id}")

    async def reindex_document(
        self, db: AsyncSession, doc_id: int
    ) -> DocumentResponse:
        """重建文档索引：清除旧向量后重新处理。"""
        document = await self._get_document_or_404(db, doc_id)

        kb_result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == document.knowledge_base_id
            )
        )
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            raise ResourceNotFoundError("文档所属知识库不存在")

        # 清除旧向量
        self.chroma_manager.delete_by_metadata(
            collection_name=kb.collection_name,
            metadata_key="document_id",
            metadata_value=str(doc_id),
        )

        document.status = "processing"
        await db.commit()

        try:
            # 在线程中运行同步处理，避免阻塞事件循环
            chunk_count = await asyncio.to_thread(
                self._process_and_store_sync,
                file_path=document.file_path,
                file_type=document.file_type,
                collection_name=kb.collection_name,
                doc_id=document.id,
                filename=document.filename,
                kb_id=kb.id,
            )
            document.status = "completed"
            document.chunk_count = chunk_count
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"重建索引失败: id={doc_id}, error={exc}")
            document.status = "failed"
            await db.commit()
            await db.refresh(document)
            raise FileProcessingError(f"重建索引失败: {exc}")

        await db.commit()
        await db.refresh(document)
        logger.info(f"文档索引已重建: id={doc_id}, chunks={chunk_count}")
        return DocumentResponse.model_validate(document)

    async def get_processing_status(
        self, db: AsyncSession, kb_id: int
    ) -> dict:
        """获取知识库下文档处理状态汇总。"""
        result = await db.execute(
            select(Document.status, func.count(Document.id))
            .where(Document.knowledge_base_id == kb_id)
            .group_by(Document.status)
        )
        status_counts = {row[0]: row[1] for row in result.all()}

        return {
            "knowledge_base_id": kb_id,
            "processing": status_counts.get("processing", 0),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "total": sum(status_counts.values()),
        }

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    def _trigger_processing_async(
        self,
        doc_id: int,
        file_path: str,
        file_type: str,
        collection_name: str,
        filename: str,
        kb_id: int,
    ) -> None:
        """异步触发文档解析、向量化与入库（fire-and-forget）。

        使用独立的数据库会话，避免与请求会话的生命周期冲突。
        处理失败时将文档状态更新为 failed，仅记录日志。
        """
        from app.db.session import AsyncSessionLocal
        from app.models.document import Document as DocModel

        async def _run_processing() -> None:
            async with AsyncSessionLocal() as session:
                try:
                    # 在线程中运行同步处理，避免阻塞事件循环导致 HTTP 响应超时
                    chunk_count = await asyncio.to_thread(
                        self._process_and_store_sync,
                        file_path=file_path,
                        file_type=file_type,
                        collection_name=collection_name,
                        doc_id=doc_id,
                        filename=filename,
                        kb_id=kb_id,
                    )
                    # 更新文档状态为已完成
                    doc = await session.get(DocModel, doc_id)
                    if doc is not None:
                        doc.status = "completed"
                        doc.chunk_count = chunk_count
                        await session.commit()
                    logger.info(
                        f"文档处理完成: id={doc_id}, chunks={chunk_count}"
                    )
                    # 处理完成后异步触发智能总结
                    self._trigger_summary_async(doc_id)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(f"文档处理失败: id={doc_id}, error={exc}")
                    doc = await session.get(DocModel, doc_id)
                    if doc is not None:
                        doc.status = "failed"
                        await session.commit()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_run_processing())
            logger.info(f"已异步触发文档处理任务: doc_id={doc_id}")
        except RuntimeError as exc:
            logger.warning(
                f"无法异步触发处理任务（无事件循环）: doc_id={doc_id}, error={exc}"
            )

    def _trigger_summary_async(self, document_id: int) -> None:
        """异步触发文档智能总结（fire-and-forget）。

        使用独立的数据库会话，避免与请求会话的生命周期冲突。
        总结失败不影响文档入库结果，仅记录日志与状态。
        """
        # 延迟导入，避免循环依赖与启动时初始化开销
        from app.db.session import AsyncSessionLocal
        from app.services.summary_service import summary_service

        async def _run_summary() -> None:
            async with AsyncSessionLocal() as session:
                try:
                    await summary_service.summarize_document(session, document_id)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        f"异步触发文档总结失败: doc_id={document_id}, error={exc}"
                    )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_run_summary())
            logger.info(f"已异步触发文档总结任务: doc_id={document_id}")
        except RuntimeError as exc:
            # 无事件循环时退化为同步日志告警
            logger.warning(
                f"无法异步触发总结任务（无事件循环）: doc_id={document_id}, error={exc}"
            )

    async def _get_document_or_404(
        self, db: AsyncSession, doc_id: int
    ) -> Document:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()
        if document is None:
            raise ResourceNotFoundError("文档不存在")
        return document

    def _parse_file(
        self, file_path: str, file_type: str
    ) -> List[dict]:
        """解析文件为分段列表。

        Args:
            file_path: 文件磁盘路径。
            file_type: 文件类型标识（pdf/docx/txt）。

        Returns:
            分段列表，元素为 ``{"text": str, "page": Optional[int], "paragraph": Optional[int]}``。
        """
        sections: List[dict] = []
        if file_type == "pdf":
            pages = self.pdf_processor.extract_pages(file_path)
            for page in pages:
                sections.append(
                    {
                        "text": page.get("text", ""),
                        "page": page.get("page"),
                        "paragraph": None,
                    }
                )
        elif file_type == "docx":
            paragraphs = self.docx_processor.extract_paragraphs(file_path)
            full_text = "\n".join(
                p.get("text", "") for p in paragraphs if p.get("text")
            )
            sections.append({"text": full_text, "page": None, "paragraph": None})
        else:  # txt
            text = self.txt_processor.extract_text(file_path)
            sections.append({"text": text, "page": None, "paragraph": None})
        return sections

    def _process_and_store_sync(
        self,
        file_path: str,
        file_type: str,
        collection_name: str,
        doc_id: int,
        filename: str,
        kb_id: int,
    ) -> int:
        """解析、清洗、切片、向量化并入库（同步方法，应在线程中调用）。

        Returns:
            实际写入的切片数量。
        """
        sections = self._parse_file(file_path, file_type)

        texts: List[str] = []
        metadatas: List[dict] = []
        ids: List[str] = []
        chunk_index = 0

        for section in sections:
            raw_text = section.get("text", "") or ""
            cleaned = self.text_cleaner.clean(raw_text)
            if not cleaned:
                continue
            chunks = self.splitter.split_recursively(cleaned)
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                texts.append(chunk)
                # 构建元数据，过滤 None 值（ChromaDB 不接受 None）
                meta: dict = {
                    "document_id": str(doc_id),
                    "file_name": filename,
                    "knowledge_base_id": str(kb_id),
                    "chunk_index": chunk_index,
                    "source": filename,
                }
                page = section.get("page")
                if page is not None:
                    meta["page"] = page
                paragraph = section.get("paragraph")
                if paragraph is not None:
                    meta["paragraph"] = paragraph
                metadatas.append(meta)
                ids.append(f"doc{doc_id}_chunk{chunk_index}_{uuid4().hex[:6]}")
                chunk_index += 1

        if not texts:
            logger.warning(f"文档未产生有效切片: doc_id={doc_id}")
            return 0

        # 向量化：优先使用 EmbeddingFactory，失败则回退至 ChromaDB 默认嵌入
        embeddings: Optional[List[List[float]]] = None
        try:
            embedder = self.embedding_factory.get_embedder()
            embeddings = embedder.embed_documents(texts)
            logger.info(f"向量化完成: doc_id={doc_id}, count={len(embeddings)}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"EmbeddingFactory 向量化失败，回退至 ChromaDB 默认嵌入: {exc}"
            )
            embeddings = None

        self.chroma_manager.add_documents(
            collection_name=collection_name,
            texts=texts,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )
        logger.info(
            f"文档入库完成: doc_id={doc_id}, collection={collection_name}, "
            f"chunks={len(texts)}"
        )
        return len(texts)


# 模块级单例
document_service = DocumentService()
