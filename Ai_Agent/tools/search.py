"""SerpAPI 搜索工具 - 提供网络搜索功能"""
from typing import List, Dict, Optional
from serpapi import GoogleSearch
import os


class SearchTool:
    """SerpAPI 搜索工具"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化搜索工具

        Args:
            api_key: SerpAPI API Key，如果不提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY", "")
        if not self.api_key:
            print("[WARNING] SERPAPI_KEY not configured. Search functionality will be unavailable.")

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        执行网络搜索

        Args:
            query: 搜索查询
            num_results: 返回结果数量

        Returns:
            搜索结果列表
        """
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not configured. Please set it in .env file.")

        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                "engine": "google"
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # 提取有机搜索结果
            organic_results = results.get("organic_results", [])

            formatted_results = []
            for result in organic_results[:num_results]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0)
                })

            print(f"[INFO] Found {len(formatted_results)} search results for query: {query}")
            return formatted_results

        except Exception as e:
            print(f"[ERROR] Search failed: {str(e)}")
            raise

    def get_search_context(self, query: str, num_results: int = 3) -> str:
        """
        获取搜索结果的上下文文本（用于 RAG 增强）

        Args:
            query: 搜索查询
            num_results: 返回结果数量

        Returns:
            合并的搜索结果文本
        """
        results = self.search(query, num_results)
        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[搜索结果 {i}]\n"
                f"标题: {result['title']}\n"
                f"链接: {result['link']}\n"
                f"摘要: {result['snippet']}"
            )

        return "\n\n".join(context_parts)
