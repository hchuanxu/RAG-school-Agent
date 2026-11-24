"""LLM 工厂。

根据 LLM_PROVIDER 配置创建 ChatOpenAI 实例（Ollama 兼容 OpenAI API），
统一管理 LLM 实例的创建方式，避免分散在各节点中的重复代码。
"""
from typing import Optional

from langchain_openai import ChatOpenAI
from loguru import logger

from app.config import settings


def create_chat_llm(
    temperature: float = 0.3,
    model: Optional[str] = None,
) -> ChatOpenAI:
    """创建 ChatOpenAI 实例。

    根据 ``LLM_PROVIDER`` 自动选择 OpenAI / Ollama 的 base_url 和 api_key。

    Args:
        temperature: 模型温度参数。
        model: 模型名，不传则使用 ``settings.LLM_MODEL``。

    Returns:
        配置好的 ``ChatOpenAI`` 实例。
    """
    if settings.LLM_PROVIDER == "ollama":
        base_url = f"{settings.OLLAMA_BASE_URL}/v1"
        api_key = "ollama"
        effective_model = model or settings.LLM_MODEL
        logger.info(
            f"使用 Ollama LLM: base_url={base_url}, model={effective_model}"
        )
    else:
        base_url = settings.OPENAI_API_BASE
        api_key = settings.OPENAI_API_KEY
        effective_model = model or settings.LLM_MODEL
        logger.info(
            f"使用 OpenAI 兼容 LLM: base_url={base_url}, model={effective_model}"
        )

    return ChatOpenAI(
        model=effective_model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )
