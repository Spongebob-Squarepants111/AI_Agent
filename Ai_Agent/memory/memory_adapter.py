"""LangChain Memory 适配器 - 桥接 Redis ChatMemory 和 LangChain Memory"""
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from typing import Optional
from .session_memory import ChatMemory


def create_langchain_memory(chat_memory: ChatMemory) -> ConversationBufferMemory:
    """
    从 Redis ChatMemory 创建 LangChain ConversationBufferMemory

    Args:
        chat_memory: Redis 会话记忆实例

    Returns:
        填充了历史记录的 ConversationBufferMemory
    """
    # 创建 LangChain Memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="output"
    )

    # 从 Redis 加载历史记录
    history = chat_memory.get_history()

    # 填充到 LangChain Memory
    for msg in history:
        if msg["role"] == "user":
            memory.chat_memory.add_message(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            memory.chat_memory.add_message(AIMessage(content=msg["content"]))

    return memory


def save_conversation_to_redis(
    chat_memory: ChatMemory,
    user_message: str,
    assistant_message: str
):
    """
    保存对话到 Redis

    Args:
        chat_memory: Redis 会话记忆实例
        user_message: 用户消息
        assistant_message: 助手回复
    """
    chat_memory.add_message("user", user_message)
    chat_memory.add_message("assistant", assistant_message)
