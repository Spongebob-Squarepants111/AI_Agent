"""LangChain 工具封装 - 将工具封装为 LangChain Tool 对象"""
from langchain.tools import Tool
from typing import Optional
from .search import SearchTool


def create_rag_tool(rag_retriever) -> Optional[Tool]:
    """
    创建 RAG 知识库检索工具

    Args:
        rag_retriever: RAG 检索器实例

    Returns:
        LangChain Tool 实例，如果 rag_retriever 为 None 则返回 None
    """
    if not rag_retriever:
        return None

    def search_knowledge(query: str) -> str:
        """从知识库中搜索相关信息"""
        try:
            print(f"[DEBUG] Searching knowledge base for: {query}")

            # 直接尝试搜索
            context = rag_retriever.get_context(query, k=3)

            if not context or context.strip() == "":
                # 搜索没有结果，检查是否真的没有文档
                has_docs = rag_retriever.has_documents()

                if not has_docs:
                    return "知识库为空，没有可搜索的文档。请先上传文档。"
                else:
                    return "未找到与查询相关的文档。知识库中有文档，但没有匹配您查询的内容。请尝试用不同的关键词搜索。"

            print(f"[DEBUG] Found context, length: {len(context)}")
            return context

        except Exception as e:
            print(f"[ERROR] Knowledge search error: {str(e)}")
            import traceback
            traceback.print_exc()
            return f"搜索知识库时出错: {str(e)}"

    return Tool(
        name="knowledge_search",
        description=(
            "在知识库中搜索相关信息。"
            "当用户询问关于已上传文档的问题时使用此工具。"
            "输入应该是一个搜索查询字符串。"
        ),
        func=search_knowledge
    )


def create_search_tool(search_tool: SearchTool) -> Optional[Tool]:
    """
    创建网络搜索工具

    Args:
        search_tool: 搜索工具实例

    Returns:
        LangChain Tool 实例，如果 search_tool 为 None 则返回 None
    """
    if not search_tool:
        return None

    def web_search(query: str) -> str:
        """在互联网上搜索信息"""
        try:
            context = search_tool.get_search_context(query, num_results=3)
            if not context:
                return "未找到相关搜索结果。"
            return context
        except Exception as e:
            return f"网络搜索时出错: {str(e)}"

    return Tool(
        name="web_search",
        description=(
            "在互联网上搜索最新信息。"
            "当需要实时信息、最新新闻、天气、股票价格等时使用此工具。"
            "当知识库中没有相关信息时也可以使用此工具。"
            "输入应该是一个搜索查询字符串。"
        ),
        func=web_search
    )
