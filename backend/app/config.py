"""应用配置模块。

使用 pydantic-settings 读取 .env 文件中的配置项。
"""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，从 .env 文件读取配置。"""

    # 应用配置
    APP_NAME: str = "校园多源知识库智能问答助手"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/sqlite/campus.db"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma"

    # LLM 提供商: openai / ollama
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # Ollama 配置（LLM_PROVIDER=ollama 时生效）
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # 本地Embedding模型（可选，为空则使用 OpenAI / Ollama）
    LOCAL_EMBEDDING_MODEL: str = ""

    # 文件上传
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 52428800

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # 指标采集
    METRICS_ENABLED: bool = True
    METRICS_SAMPLE_RATE: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# 全局配置单例
settings = Settings()
