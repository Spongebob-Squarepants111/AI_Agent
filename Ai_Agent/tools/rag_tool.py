"""RAG 知识库工具 - 提供文档检索功能"""
from typing import Optional


class RAGTool:
    """RAG 知识库检索工具"""

    def __init__(self, rag_retriever):
        """
        初始化 RAG 工具

        Args:
            rag_retriever: RAG 检索器实例
        """
        self.rag_retriever = rag_retriever

    def search_knowledge(self, query: str, k: int = 3) -> str:
        """
        从知识库中搜索相关信息

        Args:
            query: 搜索查询
            k: 返回文档数量

        Returns:
            相关文档的上下文文本
        """
        try:
            # 检查知识库是否有文档
            info = self.rag_retriever.get_collection_info()
            vectors_count = info.get("vectors_count", 0)

            if vectors_count == 0:
                return "知识库为空，没有可搜索的文档。"

            # 搜索相关文档
            context = self.rag_retriever.get_context(query, k=k)

            if not context:
                return "未找到相关文档。"

            return context

        except Exception as e:
            return f"搜索知识库时出错: {str(e)}"

    def get_collection_info(self) -> dict:
        """
        获取知识库信息

        Returns:
            知识库统计信息
        """
        try:
            return self.rag_retriever.get_collection_info()
        except Exception as e:
            return {"error": str(e)}
