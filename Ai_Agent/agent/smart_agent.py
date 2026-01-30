"""智能 Agent - 自动选择使用 RAG 或搜索工具"""
from typing import Optional, Dict, Any, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import json


class SmartAgent:
    """智能 Agent - 根据用户查询自动选择合适的工具"""

    def __init__(self, rag_retriever=None, search_tool=None):
        """
        初始化智能 Agent

        Args:
            rag_retriever: RAG 检索器实例
            search_tool: 搜索工具实例
        """
        self.rag_retriever = rag_retriever
        self.search_tool = search_tool

        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )

    def _has_knowledge_base(self) -> bool:
        """
        检查知识库是否有文档

        Returns:
            True 如果知识库中有文档，否则 False
        """
        if not self.rag_retriever:
            return False

        try:
            info = self.rag_retriever.get_collection_info()
            vectors_count = info.get("vectors_count", 0)
            print(f"[INFO] Knowledge base has {vectors_count} vectors")
            return vectors_count > 0
        except Exception as e:
            print(f"[WARNING] Failed to check knowledge base: {e}")
            return False

    def _check_if_unknown(self, response: str) -> bool:
        """
        检查 AI 的回答是否表示不知道

        Args:
            response: AI 的回答

        Returns:
            True 如果 AI 表示不知道，否则 False
        """
        unknown_indicators = [
            # 中文 - 直接表示不知道
            "不知道", "不清楚", "不了解", "不确定",
            # 中文 - 无法提供/回答
            "无法回答", "无法提供", "无法查询", "无法获取", "无法访问",
            "无法实时", "无法直接", "无法确定",
            # 中文 - 没有信息
            "没有信息", "没有数据", "没有相关",
            # 中文 - 抱歉/遗憾
            "抱歉", "很遗憾", "对不起",
            # 英文 - 直接表示不知道
            "don't know", "do not know", "not sure", "unclear", "uncertain",
            # 英文 - 无法提供/回答
            "cannot answer", "cannot provide", "cannot get", "cannot access",
            "unable to answer", "unable to provide", "unable to get", "unable to access",
            "can't answer", "can't provide", "can't get", "can't access",
            # 英文 - 没有信息
            "no information", "no data", "don't have information",
            # 英文 - 抱歉
            "sorry", "apologize", "unfortunately"
        ]
        response_lower = response.lower()

        # 检查是否包含任何关键词
        is_unknown = any(indicator in response_lower for indicator in unknown_indicators)

        # 打印 debug 信息
        if is_unknown:
            matched_indicators = [ind for ind in unknown_indicators if ind in response_lower]
            print(f"[DEBUG] Detected 'unknown' response, matched keywords: {matched_indicators}")

        return is_unknown

    def _generate_search_query(self, query: str, chat_history: list = None) -> str:
        """
        基于当前查询和对话历史生成更好的搜索查询

        Args:
            query: 当前用户查询
            chat_history: 对话历史

        Returns:
            优化后的搜索查询
        """
        # 如果查询很短（可能是简单回复如"需要"、"是的"等），从历史中提取真实意图
        if len(query) <= 5 and chat_history:
            # 从历史中找到最近的用户问题
            for msg in reversed(chat_history):
                if hasattr(msg, 'type') and msg.type == 'human' and len(msg.content) > 5:
                    print(f"[DEBUG] Using previous user query for search: {msg.content}")
                    return msg.content

        return query

    def chat(self, query: str, chat_history: list = None) -> Dict[str, Any]:
        """
        处理用户查询

        新的决策逻辑：
        1. 检查知识库是否有文档
        2. 如果有文档 → 使用 RAG 知识增强
        3. 如果没有文档 → 直接回答
        4. 如果 AI 表示不知道 → 调用 SerpAPI 搜索

        Args:
            query: 用户查询
            chat_history: 对话历史

        Returns:
            包含响应和使用的工具信息的字典
        """
        tool_used = "none"
        context = ""

        # 步骤 1: 检查知识库是否有文档
        has_knowledge = self._has_knowledge_base()

        if has_knowledge:
            # 步骤 2: 如果有文档，使用 RAG
            print("[INFO] Knowledge base has documents, using RAG")
            try:
                context = self.rag_retriever.get_context(query, k=3)
                if context:
                    tool_used = "knowledge"
                    print(f"[INFO] Retrieved context from knowledge base, length: {len(context)}")
            except Exception as e:
                print(f"[WARNING] Knowledge search failed: {e}")

        # 构建消息
        messages = []

        # 系统提示词
        system_prompt = """你是一个友好、专业的 BCI（脑机接口）智能助手。

你的特点：
- 友好、耐心、专业
- 回答准确、简洁
- 善于理解用户意图
- 能够提供情感化和个性化的回答
- 专注于为脑机接口用户提供优质的交互体验"""

        if context:
            system_prompt += f"\n\n以下是从知识库中检索到的相关信息：\n\n{context}\n\n请基于上述知识库内容回答用户的问题。"

        messages.append(SystemMessage(content=system_prompt))

        # 添加历史消息
        if chat_history:
            messages.extend(chat_history)

        # 添加当前用户消息
        messages.append(HumanMessage(content=query))

        # 调用 LLM 获取初始回答
        try:
            response = self.llm.invoke(messages)
            initial_response = response.content
            print(f"[DEBUG] LLM initial response: {initial_response}")

            # 步骤 4: 如果 AI 表示不知道且有搜索工具，使用搜索
            if not has_knowledge and self._check_if_unknown(initial_response) and self.search_tool:
                print("[INFO] AI doesn't know the answer, using web search")
                try:
                    # 生成更好的搜索查询
                    search_query = self._generate_search_query(query, chat_history)
                    print(f"[DEBUG] Generated search query: {search_query}")

                    search_context = self.search_tool.get_search_context(search_query, num_results=3)
                    if search_context:
                        tool_used = "search"
                        print(f"[INFO] Retrieved search results, length: {len(search_context)}")

                        # 重新构建消息，加入搜索结果
                        messages = []
                        system_prompt_with_search = system_prompt + f"\n\n以下是从互联网搜索到的相关信息：\n\n{search_context}\n\n请基于上述搜索结果回答用户的问题，并在适当的地方引用来源链接。"
                        messages.append(SystemMessage(content=system_prompt_with_search))

                        if chat_history:
                            messages.extend(chat_history)

                        messages.append(HumanMessage(content=query))

                        # 重新调用 LLM
                        response = self.llm.invoke(messages)
                        initial_response = response.content
                        print(f"[DEBUG] LLM response after search: {initial_response}")
                except Exception as e:
                    print(f"[WARNING] Web search failed: {e}")

            return {
                "response": initial_response,
                "tool_used": tool_used,
                "has_context": bool(context) or (tool_used == "search")
            }
        except Exception as e:
            print(f"[ERROR] LLM invocation failed: {e}")
            raise

    async def chat_stream(self, query: str, chat_history: list = None) -> AsyncGenerator[str, None]:
        """
        流式处理用户查询

        Args:
            query: 用户查询
            chat_history: 对话历史

        Yields:
            SSE 格式的数据流
        """
        tool_used = "none"
        context = ""

        # 步骤 1: 检查知识库是否有文档
        has_knowledge = self._has_knowledge_base()

        if has_knowledge:
            print("[INFO] Knowledge base has documents, using RAG")
            try:
                context = self.rag_retriever.get_context(query, k=3)
                if context:
                    tool_used = "knowledge"
                    print(f"[INFO] Retrieved context from knowledge base")
            except Exception as e:
                print(f"[WARNING] Knowledge search failed: {e}")

        # 构建消息
        messages = []
        system_prompt = """你是一个友好、专业的 BCI（脑机接口）智能助手。

你的特点：
- 友好、耐心、专业
- 回答准确、简洁
- 善于理解用户意图
- 能够提供情感化和个性化的回答
- 专注于为脑机接口用户提供优质的交互体验"""

        if context:
            system_prompt += f"\n\n以下是从知识库中检索到的相关信息：\n\n{context}\n\n请基于上述知识库内容回答用户的问题。"

        messages.append(SystemMessage(content=system_prompt))

        if chat_history:
            messages.extend(chat_history)

        messages.append(HumanMessage(content=query))

        # 发送元数据
        yield f"data: {json.dumps({'type': 'metadata', 'tool_used': tool_used, 'has_context': bool(context)})}\n\n"

        try:
            # 流式调用 LLM
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"

            # 打印完整的 LLM 响应
            print(f"[DEBUG] LLM stream response: {full_response}")

            # 如果 AI 不知道且需要搜索
            if not has_knowledge and self._check_if_unknown(full_response) and self.search_tool:
                print("[INFO] AI doesn't know, using web search")
                yield f"data: {json.dumps({'type': 'status', 'message': '正在搜索相关信息...'})}\n\n"

                try:
                    # 生成更好的搜索查询
                    search_query = self._generate_search_query(query, chat_history)
                    print(f"[DEBUG] Generated search query: {search_query}")

                    search_context = self.search_tool.get_search_context(search_query, num_results=3)
                    if search_context:
                        tool_used = "search"

                        # 重新构建消息
                        messages = []
                        system_prompt_with_search = system_prompt + f"\n\n以下是从互联网搜索到的相关信息：\n\n{search_context}\n\n请基于上述搜索结果回答用户的问题，并在适当的地方引用来源链接。"
                        messages.append(SystemMessage(content=system_prompt_with_search))

                        if chat_history:
                            messages.extend(chat_history)

                        messages.append(HumanMessage(content=query))

                        # 清空之前的回答
                        yield f"data: {json.dumps({'type': 'clear'})}\n\n"
                        yield f"data: {json.dumps({'type': 'metadata', 'tool_used': 'search', 'has_context': True})}\n\n"

                        # 流式输出新的回答
                        search_response = ""
                        async for chunk in self.llm.astream(messages):
                            if chunk.content:
                                search_response += chunk.content
                                yield f"data: {json.dumps({'type': 'content', 'content': chunk.content})}\n\n"

                        # 打印搜索后的 LLM 响应
                        print(f"[DEBUG] LLM response after search: {search_response}")
                except Exception as e:
                    print(f"[WARNING] Web search failed: {e}")

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            print(f"[ERROR] Stream failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
