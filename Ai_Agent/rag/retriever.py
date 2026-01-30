"""RAG 检索器 - 整合文档处理和向量检索"""
from typing import List, Optional
from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from langchain_core.documents import Document
import os


class RAGRetriever:
    """RAG 检索器 - 提供完整的 RAG 功能"""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        use_memory: bool = True,  # 默认使用内存模式
    ):
        """
        初始化 RAG 检索器

        Args:
            collection_name: 向量存储集合名称
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠大小
            use_memory: 是否使用内存模式（默认 True）
        """
        self.doc_processor = DocumentProcessor(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        self.vector_store = VectorStore(
            collection_name=collection_name,
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
            use_memory=use_memory,
        )

    def add_text(self, text: str, metadata: Optional[dict] = None) -> int:
        """
        添加文本到知识库

        Args:
            text: 文本内容
            metadata: 元数据

        Returns:
            添加的文档数量
        """
        documents = self.doc_processor.load_text(text, metadata)
        self.vector_store.add_documents(documents)
        return len(documents)

    def add_pdf(self, pdf_path: str) -> int:
        """
        添加 PDF 文件到知识库

        Args:
            pdf_path: PDF 文件路径

        Returns:
            添加的文档数量
        """
        documents = self.doc_processor.load_pdf(pdf_path)
        self.vector_store.add_documents(documents)
        return len(documents)

    def add_url(self, url: str) -> int:
        """
        从 URL 添加内容到知识库

        Args:
            url: 网页 URL

        Returns:
            添加的文档数量
        """
        documents = self.doc_processor.load_url(url)
        self.vector_store.add_documents(documents)
        return len(documents)

    def add_text_file(self, file_path: str) -> int:
        """
        添加文本文件到知识库

        Args:
            file_path: 文本文件路径

        Returns:
            添加的文档数量
        """
        documents = self.doc_processor.load_text_file(file_path)
        self.vector_store.add_documents(documents)
        return len(documents)

    def search(self, query: str, k: int = 3) -> List[Document]:
        """
        搜索相关文档

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            相关文档列表
        """
        return self.vector_store.similarity_search(query, k=k)

    def get_context(self, query: str, k: int = 3) -> str:
        """
        获取查询的上下文文本

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            合并的上下文文本
        """
        documents = self.search(query, k=k)
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[文档 {i}]\n{doc.page_content}")

        return "\n\n".join(context_parts)

    def get_collection_info(self) -> dict:
        """获取知识库信息"""
        return self.vector_store.get_collection_info()
