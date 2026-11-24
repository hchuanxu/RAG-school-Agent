"""Embedding 工厂。

根据配置返回 OpenAI 或本地 HuggingFace 嵌入模型，使用单例模式缓存实例。
当外部模型不可用（网络受限/依赖缺失）时自动降级为哈希嵌入。
"""
import hashlib
from threading import Lock
from typing import List, Optional

from langchain_core.embeddings import Embeddings
from loguru import logger

from app.config import settings


class _HashEmbeddings(Embeddings):
    """哈希嵌入（离线降级方案）。

    基于字符 hash 生成固定维度的伪向量，保证接口兼容。
    仅用于无外部模型时的后备，检索质量低于真实语义嵌入。
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        text = text or ""
        vec = [0.0] * self.dim
        # 按字符滑动生成 hash，叠加到向量不同维度
        for i, ch in enumerate(text[: self.dim * 4]):
            h = int(hashlib.md5(f"{i}:{ch}".encode("utf-8")).hexdigest(), 16)
            vec[i % self.dim] += ((h % 1000) / 1000.0 - 0.5)
        # L2 归一化
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class EmbeddingFactory:
    """Embedding 工厂（单例）。

    根据 ``settings.LOCAL_EMBEDDING_MODEL`` 决定使用本地模型还是 OpenAI 模型：

    - ``LOCAL_EMBEDDING_MODEL`` 非空：使用
      :class:`langchain_community.embeddings.HuggingFaceEmbeddings`；
    - 否则：使用 :class:`langchain_openai.OpenAIEmbeddings`。

    通过 :meth:`get_embedder` 获取全局唯一实例。
    """

    _instance: Optional["EmbeddingFactory"] = None
    _lock: Lock = Lock()
    _embedder: Optional[Embeddings] = None

    def __new__(cls) -> "EmbeddingFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _build_embedder(cls) -> Embeddings:
        """构建新的 Embedding 实例。

        优先级：HuggingFace 本地模型 > Ollama Embedding > OpenAI Embedding > 哈希嵌入
        """
        local_model = (settings.LOCAL_EMBEDDING_MODEL or "").strip()
        if local_model:
            logger.info(f"使用本地 Embedding 模型: {local_model}")
            try:
                from langchain_community.embeddings import (
                    HuggingFaceEmbeddings,
                )

                embedder = HuggingFaceEmbeddings(
                    model_name=local_model,
                    model_kwargs={"local_files_only": False},
                )
                embedder.embed_query("测试")
                return embedder
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"加载 HuggingFaceEmbeddings 失败，降级为哈希嵌入: {exc}"
                )
                return _HashEmbeddings()

        # Ollama 嵌入
        if settings.LLM_PROVIDER == "ollama":
            logger.info(
                f"使用 Ollama Embedding 模型: {settings.OLLAMA_EMBEDDING_MODEL}"
            )
            try:
                from langchain_community.embeddings import OllamaEmbeddings

                embedder = OllamaEmbeddings(
                    model=settings.OLLAMA_EMBEDDING_MODEL,
                    base_url=settings.OLLAMA_BASE_URL,
                )
                embedder.embed_query("测试")
                return embedder
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"加载 OllamaEmbeddings 失败，降级为哈希嵌入: {exc}"
                )
                return _HashEmbeddings()

        # OpenAI 嵌入
        logger.info(
            f"使用 OpenAI Embedding 模型: {settings.EMBEDDING_MODEL}"
        )
        try:
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"加载 OpenAIEmbeddings 失败，降级为哈希嵌入: {exc}"
            )
            return _HashEmbeddings()

    def get_embedder(self) -> Embeddings:
        """获取全局唯一的 Embedding 实例。

        Returns:
            ``Embeddings`` 实例。
        """
        if self._embedder is None:
            with self._lock:
                if self._embedder is None:
                    self._embedder = self._build_embedder()
                    logger.debug("Embedding 实例已创建并缓存")
        return self._embedder

    @classmethod
    def reset(cls) -> None:
        """重置缓存的实例（主要用于测试或配置热更新）。"""
        with cls._lock:
            cls._embedder = None
            logger.debug("Embedding 实例缓存已重置")
