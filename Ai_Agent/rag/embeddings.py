"""文本嵌入模块 - 使用通义千问 embedding API"""
from typing import List
from langchain_community.embeddings import DashScopeEmbeddings


class QwenEmbeddings:
    def __init__(self):
        """初始化通义千问嵌入模型"""
        self.embedding_model = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=None  # 从环境变量自动读取
        )
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """对文本列表进行嵌入"""
        return self.embedding_model.embed_documents(texts)
    
    def embed_query(self, query: str) -> List[float]:
        """对单个查询进行嵌入"""
        return self.embedding_model.embed_query(query)


# 全局实例
qwen_embeddings = QwenEmbeddings()


def get_embedding(text: str) -> List[float]:
    """获取单个文本的嵌入向量"""
    return qwen_embeddings.embed_query(text)


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """获取多个文本的嵌入向量"""
    return qwen_embeddings.embed_texts(texts)