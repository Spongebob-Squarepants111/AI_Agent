"""短期记忆模块 - 使用 Redis 存储对话历史"""
from typing import Optional, List, Dict
import redis
import json
import os
import uuid
from datetime import datetime


class ChatMemory:
    """使用 Redis 存储对话记忆"""
    
    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.max_history = max_history
        self.key = f"chat_history:{session_id}"
        
        # Redis 连接
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            password=os.getenv("REDIS_PASSWORD", None),
            decode_responses=True
        )
    
    def add_message(self, role: str, content: str):
        """添加一条消息到历史记录"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.rpush(self.key, json.dumps(message, ensure_ascii=False))
        # 保持最大历史记录数
        self.redis_client.ltrim(self.key, -self.max_history * 2, -1)
        # 设置过期时间（24小时）
        self.redis_client.expire(self.key, 86400)
    
    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        messages = self.redis_client.lrange(self.key, 0, -1)
        return [json.loads(msg) for msg in messages]
    
    def get_history_string(self) -> str:
        """获取历史记录字符串格式"""
        history = self.get_history()
        if not history:
            return ""
        
        history_str = "\n以下是之前的对话历史：\n"
        for msg in history:
            role = "用户" if msg["role"] == "user" else "助手"
            history_str += f"{role}: {msg['content']}\n"
        return history_str
    
    def clear(self):
        """清空历史记录"""
        self.redis_client.delete(self.key)


def create_session_memory(session_id: str = None) -> ChatMemory:
    """创建会话记忆实例，如果未提供 session_id 则自动生成"""
    if not session_id:
        session_id = str(uuid.uuid4())
    return ChatMemory(session_id)