"""RAG 检索工具 - 用于 Agent 调用"""
from langchain.tools import BaseTool
from pydantic import Field
from typing import Type, Any
from ..rag.retriever import knowledge_retriever


class RAGSearchTool(BaseTool):
    name = "rag_search"
    description = "用于从知识库中检索相关信息的工具。当你不确定答案或需要查找特定信息时使用此工具。输入应为一个清晰的查询问题。"
    
    def _run(self, query: str) -> str:
        """执行 RAG 搜索"""
        try:
            context = knowledge_retriever.retrieve_with_context(query)
            if context:
                return context
            else:
                return "在知识库中未找到与查询相关的信息。"
        except Exception as e:
            return f"RAG 搜索过程中发生错误: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """异步执行 RAG 搜索"""
        return self._run(query)


class AddKnowledgeTool(BaseTool):
    name = "add_knowledge"
    description = "用于向知识库添加新知识的工具。输入应为要添加的知识内容。"
    
    def _run(self, content: str) -> str:
        """添加知识到知识库"""
        try:
            doc_id = knowledge_retriever.add_knowledge(content)
            return f"成功添加知识到知识库，文档ID: {doc_id}"
        except Exception as e:
            return f"添加知识时发生错误: {str(e)}"
    
    async def _arun(self, content: str) -> str:
        """异步添加知识"""
        return self._run(content)


# 工具列表
rag_tools = [RAGSearchTool()]