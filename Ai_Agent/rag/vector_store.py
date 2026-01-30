"""向量存储模块 - 使用 Qdrant 进行向量存储和检索"""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os


class VectorStore:
    """向量存储管理器"""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = True,  # 默认使用内存模式
    ):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
            host: Qdrant 服务器地址（use_memory=False 时使用）
            port: Qdrant 服务器端口（use_memory=False 时使用）
            use_memory: 是否使用内存模式（默认 True）
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.use_memory = use_memory

        # 初始化 OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )

        # 初始化 Qdrant 客户端
        if use_memory:
            # 使用内存模式，不需要外部 Qdrant 服务
            self.client = QdrantClient(":memory:")
            print("[INFO] Using Qdrant in-memory mode")
        else:
            # 使用外部 Qdrant 服务
            self.client = QdrantClient(host=host, port=port)
            print(f"[INFO] Connecting to Qdrant at {host}:{port}")

        # 确保集合存在
        self._ensure_collection()

        # 创建持久的 Qdrant vectorstore 实例
        self.vectorstore = Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )
        print(f"[INFO] Vectorstore initialized for collection: {self.collection_name}")

    def _ensure_collection(self):
        """确保集合存在，如果不存在则创建"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                # 创建集合（OpenAI embeddings 维度为 1536）
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                print(f"[INFO] Created collection: {self.collection_name}")
        except Exception as e:
            print(f"[WARNING] Could not check/create collection: {e}")
            if not self.use_memory:
                print("[INFO] Qdrant may not be running. Vector store will be unavailable.")

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储

        Args:
            documents: 文档列表

        Returns:
            文档 ID 列表
        """
        try:
            ids = self.vectorstore.add_documents(documents)
            print(f"[INFO] Added {len(documents)} documents to vector store")
            return ids
        except Exception as e:
            print(f"[ERROR] Failed to add documents: {e}")
            raise

    def similarity_search(
        self, query: str, k: int = 3, score_threshold: float = 0.0
    ) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量
            score_threshold: 相似度阈值

        Returns:
            相关文档列表
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)

            # 过滤低于阈值的结果
            filtered_results = [
                doc for doc, score in results if score >= score_threshold
            ]

            print(f"[INFO] Found {len(filtered_results)} relevant documents")
            return filtered_results
        except Exception as e:
            print(f"[ERROR] Similarity search failed: {e}")
            return []

    def delete_collection(self):
        """删除集合"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            print(f"[INFO] Deleted collection: {self.collection_name}")
        except Exception as e:
            print(f"[ERROR] Failed to delete collection: {e}")

    def get_collection_info(self) -> dict:
        """获取集合信息"""
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "storage_mode": "memory" if self.use_memory else f"{self.host}:{self.port}",
            }
        except Exception as e:
            print(f"[ERROR] Failed to get collection info: {e}")
            return {}
