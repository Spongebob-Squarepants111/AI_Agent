"""项目配置设置"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    """应用配置类"""

    # ========================================
    # LLM 配置
    # ========================================
    # OpenAI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # ========================================
    # Redis 配置（会话记忆）
    # ========================================
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # ========================================
    # Qdrant 配置（向量数据库）
    # ========================================
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "knowledge_base")

    # ========================================
    # Agent 配置
    # ========================================
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", 3))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", 0.7))
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", 10))

    # ========================================
    # 其他配置
    # ========================================
    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


# 创建全局配置实例
settings = Settings()
