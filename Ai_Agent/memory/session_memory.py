"""会话记忆模块 - 基于 Redis 的对话历史管理"""
import redis
import json
import os
from typing import List, Dict
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage


class ChatMemory:
    """基于 Redis 的会话记忆管理"""

    def __init__(self, session_id: str, redis_client: redis.Redis, max_history: int = 10):
        """
        初始化会话记忆

        Args:
            session_id: 会话ID
            redis_client: Redis 客户端
            max_history: 最大历史记录数量
        """
        self.session_id = session_id
        self.redis_client = redis_client
        self.max_history = max_history
        self.key = f"chat_history:{session_id}"

    def add_message(self, role: str, content: str):
        """
        添加消息到历史记录

        Args:
            role: 角色（user/assistant）
            content: 消息内容
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.lpush(self.key, json.dumps(message))
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

    def get_history_messages(self) -> List:
        """
        获取格式化的历史消息列表（用于 LangChain）

        Returns:
            LangChain 消息对象列表
        """
        history = self.get_history()
        messages = []

        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(SystemMessage(content=msg["content"]))

        return messages

    def clear(self):
        """清空历史记录"""
        self.redis_client.delete(self.key)


def create_session_memory(session_id: str) -> ChatMemory:
    """
    创建会话记忆实例

    Args:
        session_id: 会话ID

    Returns:
        ChatMemory 实例
    """
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    return ChatMemory(session_id, redis_client)
