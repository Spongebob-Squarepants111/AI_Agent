"""检索器模块 - 从向量数据库检索相关信息"""
from typing import List, Dict, Any
from ..rag.vector_store import vector_store


class KnowledgeRetriever:
    def __init__(self, top_k: int = 3, score_threshold: float = 0.5):
        """初始化知识检索器
        Args:
            top_k: 返回最相关的 top_k 个文档
            score_threshold: 相似度阈值，低于此值的文档会被过滤
        """
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.vector_store = vector_store
    
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """根据查询检索相关文档"""
        # 搜索相似文档
        search_results = self.vector_store.search(query, top_k=self.top_k * 2)  # 搜索更多文档以过滤
        
        # 过滤低相似度文档
        filtered_results = [
            result for result in search_results 
            if result["score"] >= self.score_threshold
        ][:self.top_k]
        
        return filtered_results
    
    def retrieve_with_context(self, query: str) -> str:
        """根据查询检索相关文档并返回格式化的上下文"""
        results = self.retrieve(query)
        
        if not results:
            return ""
        
        context_parts = ["以下是与您问题相关的知识库信息："]
        for i, result in enumerate(results, 1):
            context_parts.append(f"\n{i}. {result['content']}")
            if result['metadata']:
                context_parts.append(f"   来源信息: {result['metadata']}")
        
        return "\n".join(context_parts)
    
    def add_knowledge(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """添加知识到知识库"""
        return self.vector_store.add_document(content, metadata)
    
    def delete_knowledge(self, doc_id: str) -> bool:
        """从知识库删除文档"""
        return self.vector_store.delete_document(doc_id)


# 全局实例
knowledge_retriever = KnowledgeRetriever()