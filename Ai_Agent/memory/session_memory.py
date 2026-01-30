"""基于 Redis 的会话记忆管理"""
import redis
import json
from typing import List, Dict
from datetime import datetime
from config.settings import settings


class ChatMemory:
    """基于 Redis 的会话记忆管理类"""

    def __init__(self, session_id: str, redis_client: redis.Redis, max_history: int = None):
        """
        初始化会话记忆

        Args:
            session_id: 会话ID
            redis_client: Redis 客户端实例
            max_history: 最大历史记录数量，默认从配置读取
        """
        self.session_id = session_id
        self.redis_client = redis_client
        self.max_history = max_history or settings.MAX_HISTORY
        self.key = f"chat_history:{session_id}"

    def add_message(self, role: str, content: str):
        """
        添加消息到历史记录

        Args:
            role: 角色（user 或 assistant）
            content: 消息内容
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.lpush(self.key, json.dumps(message, ensure_ascii=False))
        # 保持历史记录在最大长度内
        self.redis_client.ltrim(self.key, 0, self.max_history - 1)

    def get_history(self) -> List[Dict]:
        """
        获取历史记录

        Returns:
            历史消息列表
        """
        messages = self.redis_client.lrange(self.key, 0, -1)
        return [json.loads(msg) for msg in reversed(messages)]

    def get_history_string(self) -> str:
        """
        获取格式化的历史记录字符串

        Returns:
            格式化的历史记录
        """
        history = self.get_history()
        if not history:
            return ""

        history_str = "\n对话历史:\n"
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            history_str += f"{role}: {msg['content']}\n"
        return history_str

    def clear(self):
        """清空历史记录"""
        self.redis_client.delete(self.key)

    def get_message_count(self) -> int:
        """
        获取历史消息数量

        Returns:
            消息数量
        """
        return self.redis_client.llen(self.key)


def create_session_memory(session_id: str) -> ChatMemory:
    """
    创建会话记忆实例

    Args:
        session_id: 会话ID

    Returns:
        ChatMemory 实例
    """
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        decode_responses=True
    )
    return ChatMemory(session_id, redis_client)
