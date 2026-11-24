"""智能总结服务。

协调文档摘要、关键条例、考点生成三个生成器，将结果持久化到数据库，
并管理文档的总结状态。支持初次生成、重新生成、查询与状态获取。
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, ResourceNotFoundError
from app.models.document import Document
from app.models.summary import GeneratedQuestion, KeyRule, Summary
from app.rag.processors.docx_processor import DOCXProcessor
from app.rag.processors.pdf_processor import PDFProcessor
from app.rag.processors.text_cleaner import TextCleaner
from app.rag.processors.txt_processor import TXTProcessor
from app.rag.summarizer.document_summarizer import DocumentSummarizer
from app.rag.summarizer.key_rules_extractor import KeyRulesExtractor
from app.rag.summarizer.question_generator import QuestionGenerator


class SummaryService:
    """智能总结服务。"""

    def __init__(self) -> None:
        self.summarizer = DocumentSummarizer()
        self.rules_extractor = KeyRulesExtractor()
        self.question_generator = QuestionGenerator()
        self.text_cleaner = TextCleaner()
        self.pdf_processor = PDFProcessor()
        self.docx_processor = DOCXProcessor()
        self.txt_processor = TXTProcessor()

    # ------------------------------------------------------------------ #
    # 主流程
    # ------------------------------------------------------------------ #
    async def summarize_document(
        self, db: AsyncSession, document_id: int
    ) -> Dict[str, Any]:
        """对指定文档生成摘要、条例与考点。

        Args:
            db: 异步数据库会话。
            document_id: 文档 ID。

        Returns:
            包含 summary / rules / questions 概要信息的字典。

        Raises:
            ResourceNotFoundError: 文档不存在。
            BusinessException: 文档状态不允许生成总结。
        """
        document = await self._get_document(db, document_id)

        # 更新状态为处理中
        document.summary_status = "processing"
        await db.commit()

        try:
            # 读取文档文本
            document_text = self._read_document_text(document)
            if not document_text.strip():
                raise BusinessException("文档内容为空，无法生成总结")

            logger.info(
                f"开始生成文档总结: doc_id={document_id}, text_len={len(document_text)}"
            )

            # 依次调用三个生成器
            summary_text = await self.summarizer.generate_summary(
                document_text, title=document.filename
            )
            rules = await self.rules_extractor.extract_rules(document_text)
            questions = await self.question_generator.generate_questions(
                document_text
            )

            # 清理旧记录并写入新记录
            await self._clear_existing(db, document_id)

            db.add(
                Summary(
                    document_id=document_id,
                    summary_text=summary_text or "（摘要生成失败）",
                )
            )
            for rule in rules:
                db.add(
                    KeyRule(
                        document_id=document_id,
                        title=rule.get("title", "")[:256],
                        content=rule.get("content", ""),
                        source_location=rule.get("source_location"),
                        category=rule.get("category"),
                        importance_score=rule.get("importance_score", 0.0),
                    )
                )
            for q in questions:
                db.add(
                    GeneratedQuestion(
                        document_id=document_id,
                        question=q.get("question", ""),
                        answer=q.get("answer", ""),
                        difficulty=q.get("difficulty", "基础"),
                        category=q.get("category"),
                        source_location=q.get("source_location"),
                    )
                )

            document.summary_status = "completed"
            await db.commit()
            logger.info(
                f"文档总结完成: doc_id={document_id}, "
                f"rules={len(rules)}, questions={len(questions)}"
            )
            return {
                "document_id": document_id,
                "summary_status": "completed",
                "summary_length": len(summary_text or ""),
                "rules_count": len(rules),
                "questions_count": len(questions),
            }
        except BusinessException:
            document.summary_status = "failed"
            await db.commit()
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"文档总结失败: doc_id={document_id}, error={exc}")
            document.summary_status = "failed"
            await db.commit()
            raise BusinessException(f"文档总结失败: {exc}")

    async def regenerate_summary(
        self, db: AsyncSession, document_id: int
    ) -> Dict[str, Any]:
        """重新生成文档总结（等价于 summarize_document）。"""
        logger.info(f"重新生成文档总结: doc_id={document_id}")
        return await self.summarize_document(db, document_id)

    # ------------------------------------------------------------------ #
    # 查询接口
    # ------------------------------------------------------------------ #
    async def get_summary(
        self, db: AsyncSession, document_id: int
    ) -> Dict[str, Any]:
        """获取文档总结详情。

        Returns:
            包含 summary / rules / questions / status 的字典。
        """
        await self._get_document(db, document_id)

        summary = await self._get_summary_record(db, document_id)
        rules = await self._get_key_rules(db, document_id)
        questions = await self._get_generated_questions(db, document_id)
        document = await self._get_document(db, document_id)

        return {
            "document_id": document_id,
            "summary_status": document.summary_status,
            "summary": summary.summary_text if summary else None,
            "summary_created_at": summary.created_at if summary else None,
            "rules": [
                {
                    "id": r.id,
                    "title": r.title,
                    "content": r.content,
                    "source_location": r.source_location,
                    "category": r.category,
                    "importance_score": r.importance_score,
                }
                for r in rules
            ],
            "questions": [
                {
                    "id": q.id,
                    "question": q.question,
                    "answer": q.answer,
                    "difficulty": q.difficulty,
                    "category": q.category,
                    "source_location": q.source_location,
                }
                for q in questions
            ],
        }

    async def get_summary_status(
        self, db: AsyncSession, document_id: int
    ) -> str:
        """获取文档总结状态。"""
        document = await self._get_document(db, document_id)
        return document.summary_status

    async def get_key_rules(
        self, db: AsyncSession, document_id: int
    ) -> List[Dict[str, Any]]:
        """获取文档的关键条例列表。"""
        await self._get_document(db, document_id)
        rules = await self._get_key_rules(db, document_id)
        return [
            {
                "id": r.id,
                "title": r.title,
                "content": r.content,
                "source_location": r.source_location,
                "category": r.category,
                "importance_score": r.importance_score,
            }
            for r in rules
        ]

    async def get_generated_questions(
        self, db: AsyncSession, document_id: int
    ) -> List[Dict[str, Any]]:
        """获取文档的考点题目列表。"""
        await self._get_document(db, document_id)
        questions = await self._get_generated_questions(db, document_id)
        return [
            {
                "id": q.id,
                "question": q.question,
                "answer": q.answer,
                "difficulty": q.difficulty,
                "category": q.category,
                "source_location": q.source_location,
            }
            for q in questions
        ]

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    async def _get_document(
        self, db: AsyncSession, document_id: int
    ) -> Document:
        """获取文档，不存在则抛出 404。"""
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        if document is None:
            raise ResourceNotFoundError("文档不存在")
        return document

    async def _get_summary_record(
        self, db: AsyncSession, document_id: int
    ) -> Optional[Summary]:
        """获取文档最新的总结记录。"""
        result = await db.execute(
            select(Summary)
            .where(Summary.document_id == document_id)
            .order_by(Summary.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_key_rules(
        self, db: AsyncSession, document_id: int
    ) -> List[KeyRule]:
        """获取文档的关键条例列表（按重要性降序）。"""
        result = await db.execute(
            select(KeyRule)
            .where(KeyRule.document_id == document_id)
            .order_by(KeyRule.importance_score.desc(), KeyRule.id.asc())
        )
        return list(result.scalars().all())

    async def _get_generated_questions(
        self, db: AsyncSession, document_id: int
    ) -> List[GeneratedQuestion]:
        """获取文档的考点题目列表。"""
        result = await db.execute(
            select(GeneratedQuestion)
            .where(GeneratedQuestion.document_id == document_id)
            .order_by(GeneratedQuestion.id.asc())
        )
        return list(result.scalars().all())

    async def _clear_existing(
        self, db: AsyncSession, document_id: int
    ) -> None:
        """清除文档已有的总结、条例、考点记录。"""
        await db.execute(
            delete(Summary).where(Summary.document_id == document_id)
        )
        await db.execute(
            delete(KeyRule).where(KeyRule.document_id == document_id)
        )
        await db.execute(
            delete(GeneratedQuestion).where(
                GeneratedQuestion.document_id == document_id
            )
        )
        await db.flush()

    def _read_document_text(self, document: Document) -> str:
        """根据文件类型读取文档全文文本。

        Args:
            document: 文档对象。

        Returns:
            清洗后的全文文本。
        """
        file_path = document.file_path
        path = Path(file_path)
        if not path.exists():
            logger.error(f"文档文件不存在: {file_path}")
            raise BusinessException("文档文件不存在，无法读取内容")

        file_type = (document.file_type or "").lower()
        try:
            if file_type == "pdf":
                text = self.pdf_processor.extract_text(file_path)
            elif file_type == "docx":
                paragraphs = self.docx_processor.extract_paragraphs(file_path)
                text = "\n".join(
                    p.get("text", "") for p in paragraphs if p.get("text")
                )
            else:  # txt / md
                text = self.txt_processor.extract_text(file_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"读取文档内容失败: {file_path} - {exc}")
            raise BusinessException(f"读取文档内容失败: {exc}")

        return self.text_cleaner.clean(text)


# 模块级单例
summary_service = SummaryService()
