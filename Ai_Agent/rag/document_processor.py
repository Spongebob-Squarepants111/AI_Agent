"""文档处理模块 - 负责文档加载、分块和向量化"""
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    WebBaseLoader
)
from langchain_core.documents import Document
import os


class DocumentProcessor:
    """文档处理器 - 处理各种格式的文档"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档处理器

        Args:
            chunk_size: 文本分块大小
            chunk_overlap: 分块重叠大小
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def load_text(self, text: str, metadata: Optional[Dict] = None) -> List[Document]:
        """
        加载纯文本

        Args:
            text: 文本内容
            metadata: 元数据

        Returns:
            文档列表
        """
        doc = Document(page_content=text, metadata=metadata or {})
        return self.text_splitter.split_documents([doc])

    def load_pdf(self, pdf_path: str) -> List[Document]:
        """
        加载 PDF 文件

        Args:
            pdf_path: PDF 文件路径

        Returns:
            文档列表
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        return self.text_splitter.split_documents(documents)

    def load_url(self, url: str) -> List[Document]:
        """
        从 URL 加载网页内容

        Args:
            url: 网页 URL

        Returns:
            文档列表
        """
        loader = WebBaseLoader(url)
        documents = loader.load()
        return self.text_splitter.split_documents(documents)

    def load_text_file(self, file_path: str) -> List[Document]:
        """
        加载文本文件

        Args:
            file_path: 文本文件路径

        Returns:
            文档列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")

        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        return self.text_splitter.split_documents(documents)
