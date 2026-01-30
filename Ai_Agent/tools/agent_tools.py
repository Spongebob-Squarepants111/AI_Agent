"""Agent 工具集 - 将 RAG 和搜索功能包装为 LangChain Tools"""
from typing import Optional, Type, Any
from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field


class KnowledgeSearchInput(BaseModel):
    """知识库搜索工具的输入"""
    query: str = Field(description="要在知识库中搜索的查询文本")
    k: int = Field(default=3, description="返回的文档数量")


class KnowledgeSearchTool(BaseTool):
    """知识库搜索工具 - 从本地知识库中检索相关信息"""
    name: str = "knowledge_search"
    description: str = """
    用于从本地知识库中搜索相关信息。
    当用户询问关于已上传文档、PDF、或之前添加到知识库的内容时使用此工具。
    适用场景：查询专业知识、文档内容、已存储的信息等。
    """
    args_schema: Type[BaseModel] = KnowledgeSearchInput
    rag_retriever: Optional[Any] = None  # 将在初始化时设置

    def _run(
        self,
        query: str,
        k: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """执行知识库搜索"""
        if not self.rag_retriever:
            return "知识库功能未启用"

        try:
            context = self.rag_retriever.get_context(query, k=k)
            if not context:
                return "在知识库中未找到相关信息"
            return context
        except Exception as e:
            return f"知识库搜索失败: {str(e)}"


class WebSearchInput(BaseModel):
    """网络搜索工具的输入"""
    query: str = Field(description="要在互联网上搜索的查询文本")
    num_results: int = Field(default=3, description="返回的搜索结果数量")


class WebSearchTool(BaseTool):
    """网络搜索工具 - 从互联网获取最新信息"""
    name: str = "web_search"
    description: str = """
    用于从互联网搜索最新信息。
    当用户询问实时信息、新闻、最新动态、或知识库中没有的信息时使用此工具。
    适用场景：查询最新新闻、实时数据、网络资源、当前事件等。
    """
    args_schema: Type[BaseModel] = WebSearchInput
    search_tool: Optional[Any] = None  # 将在初始化时设置

    def _run(
        self,
        query: str,
        num_results: int = 3,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """执行网络搜索"""
        if not self.search_tool:
            return "搜索功能未启用"

        try:
            context = self.search_tool.get_search_context(query, num_results)
            if not context:
                return "未找到相关搜索结果"
            return context
        except Exception as e:
            return f"网络搜索失败: {str(e)}"
