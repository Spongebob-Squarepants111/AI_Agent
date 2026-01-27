"""向量存储模块 - 使用 Qdrant"""
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from ..rag.embeddings import get_embedding
import uuid
import os


class QdrantVectorStore:
    def __init__(self, collection_name: str = "knowledge_base"):
        """初始化 Qdrant 向量存储"""
        self.collection_name = collection_name
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
        )
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """确保集合存在"""
        try:
            # 尝试获取集合信息，如果不存在则创建
            self.client.get_collection(self.collection_name)
        except:
            # 创建集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # 通义千问 embedding 维度
                    distance=models.Distance.COSINE
                )
            )
    
    def add_document(self, content: str, metadata: Dict[str, Any] = None, doc_id: str = None) -> str:
        """添加文档到向量存储"""
        if not doc_id:
            doc_id = str(uuid.uuid4())
        
        # 生成嵌入向量
        vector = get_embedding(content)
        
        # 准备文档数据
        payload = {
            "content": content,
            "metadata": metadata or {}
        }
        
        # 添加到 Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        
        return doc_id
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """批量添加文档"""
        doc_ids = []
        points = []
        
        for doc in documents:
            doc_id = doc.get("id") or str(uuid.uuid4())
            content = doc["content"]
            metadata = doc.get("metadata", {})
            
            # 生成嵌入向量
            vector = get_embedding(content)
            
            # 准备文档数据
            payload = {
                "content": content,
                "metadata": metadata
            }
            
            points.append(
                models.PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload=payload
                )
            )
            doc_ids.append(doc_id)
        
        # 批量添加到 Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return doc_ids
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """搜索相似文档"""
        query_vector = get_embedding(query)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "id": result.id,
                "content": result.payload["content"],
                "metadata": result.payload["metadata"],
                "score": result.score
            })
        
        return formatted_results
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[doc_id]
                )
            )
            return True
        except Exception:
            return False
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """获取单个文档"""
        results = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[doc_id]
        )
        
        if results:
            point = results[0]
            return {
                "id": point.id,
                "content": point.payload["content"],
                "metadata": point.payload["metadata"]
            }
        return None


# 全局实例
vector_store = QdrantVectorStore()