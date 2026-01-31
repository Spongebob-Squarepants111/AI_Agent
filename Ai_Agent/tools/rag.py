"""RAG 模块 - 使用 LangChain 内置组件实现文档检索"""
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os


class RAGRetriever:
    """简化的 RAG 检索器 - 使用 LangChain 内置组件"""

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """初始化 RAG 检索器"""
        self.collection_name = collection_name

        # 使用 LangChain 的文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # 使用 LangChain 的 OpenAI Embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=os.getenv("OPENAI_API_BASE")
        )

        # 创建 Qdrant 客户端（内存模式）
        self.client = QdrantClient(location=":memory:")

        # 创建集合
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            print(f"[INFO] Created collection: {collection_name}")
        except Exception as e:
            print(f"[INFO] Collection {collection_name} already exists or error: {e}")

        # 创建 LangChain Qdrant vectorstore
        self.vectorstore = Qdrant(
            client=self.client,
            collection_name=collection_name,
            embeddings=self.embeddings,
        )

    def add_pdf(self, pdf_path: str) -> int:
        """添加 PDF 文件"""
        print(f"[DEBUG] Adding PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"[DEBUG] Loaded {len(documents)} pages from PDF")
        chunks = self.text_splitter.split_documents(documents)
        print(f"[DEBUG] Split into {len(chunks)} chunks")
        self.vectorstore.add_documents(chunks)
        print(f"[DEBUG] Added {len(chunks)} chunks to vectorstore")

        # 验证添加成功
        info = self.get_collection_info()
        print(f"[DEBUG] After adding PDF, collection has {info.get('vectors_count', 0)} vectors")

        return len(chunks)

    def add_text_file(self, file_path: str) -> int:
        """添加文本文件"""
        print(f"[DEBUG] Adding text file: {file_path}")
        loader = TextLoader(file_path)
        documents = loader.load()
        print(f"[DEBUG] Loaded {len(documents)} documents from text file")
        chunks = self.text_splitter.split_documents(documents)
        print(f"[DEBUG] Split into {len(chunks)} chunks")
        self.vectorstore.add_documents(chunks)
        print(f"[DEBUG] Added {len(chunks)} chunks to vectorstore")

        # 验证添加成功
        info = self.get_collection_info()
        print(f"[DEBUG] After adding text file, collection has {info.get('vectors_count', 0)} vectors")

        return len(chunks)

    def search(self, query: str, k: int = 3) -> List[Document]:
        """搜索相关文档"""
        return self.vectorstore.similarity_search(query, k=k)

    def get_context(self, query: str, k: int = 3) -> str:
        """获取查询的上下文文本"""
        try:
            documents = self.search(query, k=k)
            print(f"[DEBUG] Search returned {len(documents)} documents for query: {query}")

            if not documents:
                return ""

            context_parts = [f"[文档 {i}]\n{doc.page_content}"
                            for i, doc in enumerate(documents, 1)]
            return "\n\n".join(context_parts)
        except Exception as e:
            print(f"[ERROR] Search error: {str(e)}")
            import traceback
            traceback.print_exc()
            return ""

    def has_documents(self) -> bool:
        """检查知识库是否有文档（通过实际搜索验证）"""
        try:
            # 尝试获取任意文档
            results = self.vectorstore.similarity_search("test", k=1)
            has_docs = len(results) > 0
            print(f"[DEBUG] has_documents check: {has_docs} (found {len(results)} docs)")
            return has_docs
        except Exception as e:
            print(f"[ERROR] has_documents check failed: {str(e)}")
            return False

    def get_collection_info(self) -> dict:
        """获取知识库信息"""
        try:
            collection = self.client.get_collection(self.collection_name)
            vectors_count = collection.vectors_count if collection.vectors_count is not None else 0

            print(f"[DEBUG] Collection info: {self.collection_name}, vectors_count: {vectors_count}")

            return {
                "collection_name": self.collection_name,
                "vectors_count": vectors_count,
                "points_count": collection.points_count if hasattr(collection, 'points_count') else vectors_count
            }
        except Exception as e:
            print(f"[ERROR] Failed to get collection info: {str(e)}")
            return {
                "collection_name": self.collection_name,
                "vectors_count": 0,
                "points_count": 0
            }
