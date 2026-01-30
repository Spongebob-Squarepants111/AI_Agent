"""文档处理模块 - 负责文档加载、分块和向量化"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
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
