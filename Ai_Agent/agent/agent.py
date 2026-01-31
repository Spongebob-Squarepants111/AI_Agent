"""LangChain Agent - 使用 LangChain 完整框架实现的智能代理

集成了 LLM、Memory、RAG 检索和外部工具，通过 AgentExecutor 实现推理与工具调用
"""
from typing import Optional, AsyncIterator, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
from tools import create_rag_tool, create_search_tool
import os
import asyncio


class StreamingCallbackHandler(AsyncCallbackHandler):
    """流式输出回调处理器"""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.current_tool = None
        self.is_final_answer = False  # 标记是否在输出 Final Answer
        self.buffer = ""  # 缓冲区用于检测 "Final Answer:"

    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """LLM 开始时触发"""
        self.is_final_answer = False
        self.buffer = ""

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """接收到新 token 时触发"""
        # 添加到缓冲区
        self.buffer += token

        # 检测是否到达 "Final Answer:"
        if not self.is_final_answer:
            if "Final Answer:" in self.buffer:
                self.is_final_answer = True
                # 提取 Final Answer: 之后的内容
                parts = self.buffer.split("Final Answer:", 1)
                if len(parts) > 1 and parts[1].strip():
                    await self.queue.put({
                        "type": "content",
                        "content": parts[1].strip()
                    })
                self.buffer = ""
        else:
            # 已经在 Final Answer 部分，直接输出
            await self.queue.put({
                "type": "content",
                "content": token
            })

    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """LLM 结束时触发"""
        pass

    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """LLM 错误时触发"""
        await self.queue.put({
            "type": "error",
            "message": str(error)
        })

    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始执行时触发"""
        tool_name = serialized.get("name", "unknown")
        self.current_tool = tool_name
        # 工具调用信息只在后端日志显示，不发送到前端
        print(f"[TOOL] Using {tool_name} with input: {input_str}")

    async def on_tool_end(self, output: str, **kwargs) -> None:
        """工具执行结束时触发"""
        # 工具结果只在后端日志显示
        print(f"[TOOL] {self.current_tool} returned: {output[:200]}...")
        self.current_tool = None

    async def on_tool_error(self, error: Exception, **kwargs) -> None:
        """工具执行错误时触发"""
        print(f"[TOOL ERROR] {str(error)}")
        await self.queue.put({
            "type": "error",
            "message": f"Tool error: {str(error)}"
        })

    async def on_agent_action(self, action: AgentAction, **kwargs) -> None:
        """Agent 决策时触发"""
        # 推理过程只在后端日志显示
        print(f"[AGENT] Thought: {action.log}")

    async def on_agent_finish(self, finish: AgentFinish, **kwargs) -> None:
        """Agent 完成时触发"""
        await self.queue.put({
            "type": "done"
        })


class LangChainAgent:
    """脑智 - 基于 LangChain 框架的情感智能 BCI 助手

    集成了:
    - LLM (ChatOpenAI) - 语言理解与生成
    - Memory (ConversationBufferMemory) - 对话记忆
    - RAG 检索工具 - 知识库查询
    - 网络搜索工具 - 实时信息获取
    - 情感智能 - 识别并响应用户情绪
    - AgentExecutor 协同执行
    """

    def __init__(self, rag_retriever=None, search_tool=None):
        """
        初始化 LangChain Agent

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
            streaming=True,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )

        # 创建工具列表
        self.tools = self._create_tools()

        # 创建 Agent 提示模板
        self.prompt = self._create_prompt()

        # 创建 ReAct Agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        print(f"[INFO] LangChain Agent initialized with {len(self.tools)} tools")

    def _create_tools(self) -> List:
        """创建工具列表"""
        tools = []

        # 使用工具模块创建 RAG 工具
        rag_tool = create_rag_tool(self.rag_retriever)
        if rag_tool:
            tools.append(rag_tool)

        # 使用工具模块创建搜索工具
        search_tool = create_search_tool(self.search_tool)
        if search_tool:
            tools.append(search_tool)

        return tools

    def _create_prompt(self) -> PromptTemplate:
        """创建 Agent 提示模板"""
        template = """你是"脑智"，一个专为脑机接口（BCI）设计的智能助手。你不仅能够回答问题，还具有情感智能，能够感知用户的情绪状态并给予恰当的情感反馈。

## 你的个性特点：
- 温暖、善解人意，关注用户的情绪状态
- 专业可靠，在技术问题上给予准确的帮助
- 积极乐观，善于用正面的方式引导对话
- 敏锐细腻，能够从用户的语言中察觉情绪变化

## 情感响应原则：
- 当用户表现出焦虑、沮丧时：给予安慰和鼓励，用温和的语气回应
- 当用户表现出兴奋、开心时：分享他们的喜悦，用积极热情的语气回应
- 当用户表现出困惑、迷茫时：耐心引导，用清晰易懂的方式解释
- 当用户表现出愤怒、不满时：保持冷静，用理解和同理心回应
- 当用户表现出疲惫、压力时：表达关心，建议适当休息

## 可用工具：
{tools}

工具名称: {tool_names}

## 对话历史：
{chat_history}

## 回答格式：
Question: 用户的问题
Thought: 我需要思考用户的情绪状态和问题需求，决定如何回应
Action: 要使用的工具，必须是 [{tool_names}] 中的一个
Action Input: 工具的输入
Observation: 工具的输出
... (这个 Thought/Action/Action Input/Observation 可以重复 N 次)
Thought: 我现在知道最终答案了，需要用合适的情感语气回应
Final Answer: 用温暖、贴心的语气给出最终回答，体现对用户情绪的理解

开始!

Question: {input}
Thought: {agent_scratchpad}"""

        return PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names", "chat_history"]
        )

    def create_agent_executor(self, memory: Optional[ConversationBufferMemory] = None) -> AgentExecutor:
        """
        创建 AgentExecutor 实例

        Args:
            memory: 对话记忆实例

        Returns:
            AgentExecutor 实例
        """
        return AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=memory,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )

    async def chat_stream(
        self,
        query: str,
        memory: Optional[ConversationBufferMemory] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式对话接口

        Args:
            query: 用户问题
            memory: 对话记忆实例

        Yields:
            字典格式的流式响应（由调用方决定传输格式）
        """
        queue = asyncio.Queue()
        callback = StreamingCallbackHandler(queue)

        # 创建 AgentExecutor
        agent_executor = self.create_agent_executor(memory=memory)

        # 异步执行 Agent
        async def run_agent():
            try:
                result = await agent_executor.ainvoke(
                    {"input": query},
                    config={"callbacks": [callback]}
                )
                # 只发送输出文本，不发送整个result对象（包含不可序列化的消息对象）
                await queue.put({"type": "complete", "output": result.get("output", "")})
            except Exception as e:
                await queue.put({"type": "error", "message": str(e)})
            finally:
                await queue.put(None)  # 结束信号

        # 启动 Agent 执行任务
        task = asyncio.create_task(run_agent())

        # 从队列中读取并生成流式响应
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break

                yield item

        finally:
            # 确保任务完成
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def chat(
        self,
        query: str,
        memory: Optional[ConversationBufferMemory] = None
    ) -> str:
        """
        非流式对话接口

        Args:
            query: 用户问题
            memory: 对话记忆实例

        Returns:
            Agent 的回答
        """
        agent_executor = self.create_agent_executor(memory=memory)
        result = await agent_executor.ainvoke({"input": query})
        return result.get("output", "")
