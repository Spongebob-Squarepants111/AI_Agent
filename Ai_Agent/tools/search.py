"""SerpAPI 搜索工具 - 用于实时信息检索"""
from langchain.tools import BaseTool
from pydantic import Field
from typing import Type, Any
import os
import requests
from urllib.parse import urlencode


class SerpAPITool(BaseTool):
    name = "serpapi_search"
    description = "用于搜索实时信息的工具。当你需要获取最新信息、统计数据、新闻或事实核查时使用此工具。输入应为一个具体的问题或搜索查询。"
    
    def _run(self, query: str) -> str:
        """执行 SerpAPI 搜索"""
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            return "错误：未配置 SERPAPI_KEY 环境变量。无法执行搜索。"
        
        try:
            # 构建请求参数
            params = {
                'q': query,
                'api_key': api_key,
                'hl': 'zh',
                'gl': 'CN'
            }
            
            # 发送请求到 SerpAPI
            response = requests.get('https://serpapi.com/search', params=params)
            response.raise_for_status()
            
            # 解析结果
            data = response.json()
            
            # 提取搜索结果
            if 'organic_results' in data:
                results = []
                for i, result in enumerate(data['organic_results'][:3]):  # 取前3个结果
                    title = result.get('title', '')
                    snippet = result.get('snippet', '')
                    link = result.get('link', '')
                    
                    results.append(f"{i+1}. {title}\n   {snippet}\n   来源: {link}")
                
                return "\n\n".join(results)
            else:
                return "未找到相关搜索结果。"
        
        except requests.exceptions.RequestException as e:
            return f"搜索请求失败: {str(e)}"
        except Exception as e:
            return f"搜索过程中发生错误: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """异步执行搜索"""
        return self._run(query)


# 工具列表
search_tools = [SerpAPITool()]