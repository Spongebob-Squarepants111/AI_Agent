from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import redis
import json
from typing import Optional, List, Dict
from datetime import datetime
import uuid
from rag import RAGRetriever
from tools import SearchTool
from agent import SmartAgent

# 加载 .env 文件中的环境变量
load_dotenv()

# ========================================
# Redis 会话记忆管理
# ========================================
class ChatMemory:
    """基于 Redis 的会话记忆管理"""
    def __init__(self, session_id: str, redis_client: redis.Redis, max_history: int = 10):
        self.session_id = session_id
        self.redis_client = redis_client
        self.max_history = max_history
        self.key = f"chat_history:{session_id}"

    def add_message(self, role: str, content: str):
        """添加消息到历史记录"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.redis_client.lpush(self.key, json.dumps(message))
        # 保持历史记录在最大长度内
        self.redis_client.ltrim(self.key, 0, self.max_history - 1)

    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        messages = self.redis_client.lrange(self.key, 0, -1)
        return [json.loads(msg) for msg in reversed(messages)]

    def get_history_messages(self) -> List:
        """获取格式化的历史消息列表（用于 LangChain）"""
        history = self.get_history()
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(SystemMessage(content=msg["content"]))
        return messages

    def clear(self):
        """清空历史记录"""
        self.redis_client.delete(self.key)

def create_session_memory(session_id: str) -> ChatMemory:
    """创建会话记忆实例"""
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        decode_responses=True
    )
    return ChatMemory(session_id, redis_client)

# ========================================
# AI 助手类
# ========================================
class Assistant:
    """基于 OpenAI 的智能助手"""
    def __init__(self, memory: Optional[ChatMemory] = None):
        # 系统提示词
        self.system_prompt = """你是一个友好、专业的 BCI（脑机接口）智能助手。你可以帮助用户回答问题、提供建议和完成各种任务。

你的特点：
- 友好、耐心、专业
- 回答准确、简洁
- 善于理解用户意图
- 能够提供情感化和个性化的回答
- 专注于为脑机接口用户提供优质的交互体验"""

        self.chat_model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )
        self.memory = memory

    def chat(self, query: str) -> str:
        """处理用户查询"""
        try:
            # 构建消息列表
            messages = [SystemMessage(content=self.system_prompt)]

            # 添加历史记录
            if self.memory:
                history_messages = self.memory.get_history_messages()
                messages.extend(history_messages)

            # 添加当前用户消息
            messages.append(HumanMessage(content=query))

            # 调用 LLM
            response = self.chat_model.invoke(messages)

            # 保存对话到记忆
            if self.memory:
                self.memory.add_message("user", query)
                self.memory.add_message("assistant", response.content)

            return response.content
        except Exception as e:
            print(f"[ERROR] Chat error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e

# ========================================
# FastAPI 应用
# ========================================
app = FastAPI(
    title="BCI Assistant API",
    description="基于 OpenAI 的脑机接口智能助手 API",
    version="1.0.0"
)

# 添加 CORS 中间件（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# 初始化 RAG 检索器
# ========================================
try:
    rag_retriever = RAGRetriever(
        collection_name=os.getenv("QDRANT_COLLECTION", "knowledge_base"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
    )
    print("[INFO] RAG retriever initialized successfully")
except Exception as e:
    print(f"[WARNING] RAG retriever initialization failed: {e}")
    print("[INFO] RAG features will be unavailable")
    rag_retriever = None

# ========================================
# 初始化搜索工具
# ========================================
try:
    search_tool = SearchTool(api_key=os.getenv("SERPAPI_KEY"))
    print("[INFO] Search tool initialized successfully")
except Exception as e:
    print(f"[WARNING] Search tool initialization failed: {e}")
    print("[INFO] Search features will be unavailable")
    search_tool = None

# ========================================
# 初始化智能 Agent
# ========================================
smart_agent = None
try:
    smart_agent = SmartAgent(rag_retriever=rag_retriever, search_tool=search_tool)
    print("[INFO] Smart Agent initialized successfully")
except Exception as e:
    print(f"[WARNING] Smart Agent initialization failed: {e}")
    print("[INFO] Agent features will be unavailable")

@app.get("/api")
def read_root():
    """API 根路径，返回欢迎信息"""
    return {
        "message": "Welcome to BCI Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.post("/chat")
def chat(query: str, session_id: Optional[str] = None):
    """
    聊天接口（支持记忆功能）

    - query: 用户输入的问题
    - session_id: 会话ID，用于匹配历史记录。如果不提供，将自动生成新的会话
    """
    print(f"[DEBUG] /chat endpoint called with query: {query}, session_id: {session_id}")
    try:
        # 如果没有提供 session_id，生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())

        # 创建记忆实例
        memory = create_session_memory(session_id)

        # 创建助手
        assistant = Assistant(memory=memory)
        print("[DEBUG] Assistant initialized with memory")

        # 处理查询
        response = assistant.chat(query)

        # 返回结果时包含 session_id
        result = {
            "session_id": session_id,
            "response": response
        }
        print(f"[DEBUG] Returning result: {result}")
        return result
    except Exception as e:
        print(f"[ERROR] Chat endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/simple_chat")
def simple_chat(query: str):
    """简单的聊天接口，不使用记忆，直接调用 OpenAI"""
    print(f"[DEBUG] /simple_chat endpoint called with query: {query}")
    try:
        chat_model = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )
        print("[DEBUG] Sending request to OpenAI...")

        messages = [
            SystemMessage(content="你是一个友好、专业的 AI 助手。"),
            HumanMessage(content=query)
        ]
        response = chat_model.invoke(messages)

        print(f"[DEBUG] OpenAI response received: {response.content}")
        return {"response": response.content}
    except Exception as e:
        print(f"[ERROR] Simple chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/chat/history")
def get_chat_history(session_id: str):
    """获取指定会话的历史记录"""
    try:
        memory = create_session_memory(session_id)
        history = memory.get_history()
        return {"session_id": session_id, "history": history}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/chat/history")
def clear_chat_history(session_id: str):
    """清空指定会话的历史记录"""
    try:
        memory = create_session_memory(session_id)
        memory.clear()
        return {"message": f"Session {session_id} history cleared"}
    except Exception as e:
        return {"error": str(e)}

# ========================================
# RAG 知识库管理接口
# ========================================
@app.post("/knowledge/add_text")
def add_text_to_knowledge(text: str, metadata: Optional[str] = None):
    """
    添加文本到知识库

    - text: 文本内容
    - metadata: 元数据（JSON 字符串）
    """
    if not rag_retriever:
        return {"error": "RAG功能未启用，请检查 Qdrant 配置"}

    try:
        meta_dict = json.loads(metadata) if metadata else None
        count = rag_retriever.add_text(text, meta_dict)
        return {
            "message": "文本已添加到知识库",
            "chunks_added": count
        }
    except Exception as e:
        print(f"[ERROR] Add text error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/knowledge/add_url")
def add_url_to_knowledge(url: str):
    """
    从 URL 添加内容到知识库

    - url: 网页 URL
    """
    if not rag_retriever:
        return {"error": "RAG功能未启用，请检查 Qdrant 配置"}

    try:
        count = rag_retriever.add_url(url)
        return {
            "message": f"已从 URL 添加内容到知识库",
            "url": url,
            "chunks_added": count
        }
    except Exception as e:
        print(f"[ERROR] Add URL error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/knowledge/add_pdf")
def add_pdf_to_knowledge(pdf_path: str):
    """
    添加 PDF 文件到知识库

    - pdf_path: PDF 文件路径
    """
    if not rag_retriever:
        return {"error": "RAG功能未启用，请检查 Qdrant 配置"}

    try:
        count = rag_retriever.add_pdf(pdf_path)
        return {
            "message": "PDF 已添加到知识库",
            "pdf_path": pdf_path,
            "chunks_added": count
        }
    except Exception as e:
        print(f"[ERROR] Add PDF error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/knowledge/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件到知识库（支持 PDF、TXT 等）

    - file: 上传的文件
    """
    if not rag_retriever:
        return {"error": "RAG功能未启用"}

    try:
        # 保存上传的文件
        import tempfile
        import shutil

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        # 根据文件类型处理
        file_ext = os.path.splitext(file.filename)[1].lower()

        if file_ext == '.pdf':
            count = rag_retriever.add_pdf(tmp_path)
        elif file_ext in ['.txt', '.md']:
            count = rag_retriever.add_text_file(tmp_path)
        else:
            os.unlink(tmp_path)
            return {"error": f"不支持的文件类型: {file_ext}"}

        # 删除临时文件
        os.unlink(tmp_path)

        return {
            "message": f"文件 {file.filename} 已添加到知识库",
            "filename": file.filename,
            "chunks_added": count
        }
    except Exception as e:
        print(f"[ERROR] Upload file error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/knowledge/search")
def search_knowledge(query: str, k: int = 3):
    """
    搜索知识库

    - query: 搜索查询
    - k: 返回结果数量
    """
    if not rag_retriever:
        return {"error": "RAG功能未启用，请检查 Qdrant 配置"}

    try:
        documents = rag_retriever.search(query, k=k)
        results = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in documents
        ]
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        print(f"[ERROR] Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/knowledge/info")
def get_knowledge_info():
    """获取知识库信息"""
    if not rag_retriever:
        return {"error": "RAG功能未启用，请检查 Qdrant 配置"}

    try:
        info = rag_retriever.get_collection_info()
        return info
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat_with_knowledge")
def chat_with_knowledge(query: str, session_id: Optional[str] = None, k: int = 3):
    """
    使用知识库增强的对话接口

    - query: 用户问题
    - session_id: 会话ID
    - k: 检索文档数量
    """
    print(f"[DEBUG] /chat_with_knowledge called with query: {query}")
    try:
        # 如果没有提供 session_id，生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())

        # 创建记忆实例
        memory = create_session_memory(session_id)

        # 创建助手
        assistant = Assistant(memory=memory)

        # 检索相关知识
        context = ""
        if rag_retriever:
            context = rag_retriever.get_context(query, k=k)
            print(f"[DEBUG] Retrieved context length: {len(context)}")

        # 构建增强的查询
        if context:
            enhanced_query = f"""基于以下知识库内容回答问题：

{context}

用户问题：{query}

请基于上述知识库内容回答问题。如果知识库中没有相关信息，请说明并尽力回答。"""
        else:
            enhanced_query = query

        # 处理查询
        response = assistant.chat(enhanced_query)

        return {
            "session_id": session_id,
            "response": response,
            "used_knowledge": bool(context)
        }
    except Exception as e:
        print(f"[ERROR] Chat with knowledge error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ========================================
# Agent 对话接口
# ========================================
@app.post("/agent_chat")
def agent_chat(query: str, session_id: Optional[str] = None):
    """
    Agent 智能对话接口 - 自动选择使用知识库或网络搜索

    - query: 用户问题
    - session_id: 会话ID（可选）
    """
    if not smart_agent:
        return {"error": "Agent 功能未启用，请检查工具配置"}

    print(f"[DEBUG] /agent_chat called with query: {query}")
    try:
        # 如果没有提供 session_id，生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())

        # 创建记忆实例
        memory = create_session_memory(session_id)

        # 获取历史消息
        chat_history = memory.get_history_messages()

        # 调用 Smart Agent
        result = smart_agent.chat(query, chat_history=chat_history)

        # 保存对话到记忆
        memory.add_message("user", query)
        memory.add_message("assistant", result["response"])

        return {
            "session_id": session_id,
            "response": result["response"],
            "tool_used": result["tool_used"],
            "has_context": result["has_context"]
        }
    except Exception as e:
        print(f"[ERROR] Agent chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/agent_chat_stream")
async def agent_chat_stream(query: str, session_id: Optional[str] = None):
    """
    Agent 智能对话接口 - 流式输出

    - query: 用户问题
    - session_id: 会话ID（可选）

    返回 SSE (Server-Sent Events) 流
    """
    if not smart_agent:
        return {"error": "Agent 功能未启用"}

    print(f"[DEBUG] /agent_chat_stream called with query: {query}")

    # 如果没有提供 session_id，生成一个新的
    if not session_id:
        session_id = str(uuid.uuid4())

    # 创建记忆实例
    memory = create_session_memory(session_id)

    # 获取历史消息
    chat_history = memory.get_history_messages()

    async def generate():
        try:
            full_response = ""
            async for chunk in smart_agent.chat_stream(query, chat_history=chat_history):
                # 收集完整回答用于保存到记忆
                if '"type": "content"' in chunk:
                    import json
                    data = json.loads(chunk.replace("data: ", "").strip())
                    if data.get("type") == "content":
                        full_response += data.get("content", "")

                yield chunk

            # 保存对话到记忆
            if full_response:
                memory.add_message("user", query)
                memory.add_message("assistant", full_response)

        except Exception as e:
            print(f"[ERROR] Stream error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# ========================================
# 搜索工具接口
# ========================================
@app.get("/search")
def web_search(query: str, num_results: int = 5):
    """
    网络搜索接口

    - query: 搜索查询
    - num_results: 返回结果数量（默认5）
    """
    if not search_tool:
        return {"error": "搜索功能未启用，请在 .env 文件中配置 SERPAPI_KEY"}

    try:
        results = search_tool.search(query, num_results)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        print(f"[ERROR] Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/agent_chat")
def agent_chat(query: str, session_id: Optional[str] = None):
    """
    Agent 智能对话接口 - 自动选择使用知识库或网络搜索

    - query: 用户问题
    - session_id: 会话ID（可选）
    """
    if not smart_agent:
        return {"error": "Agent 功能未启用，请检查工具配置"}

    print(f"[DEBUG] /agent_chat called with query: {query}")
    try:
        # 如果没有提供 session_id，生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())

        # 创建记忆实例
        memory = create_session_memory(session_id)

        # 获取历史消息
        chat_history = memory.get_history_messages()

        # 调用 Smart Agent
        result = smart_agent.chat(query, chat_history=chat_history)

        # 保存对话到记忆
        memory.add_message("user", query)
        memory.add_message("assistant", result["response"])

        return {
            "session_id": session_id,
            "response": result["response"],
            "tool_used": result["tool_used"],
            "has_context": result["has_context"]
        }
    except Exception as e:
        print(f"[ERROR] Agent chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/chat_with_search")
def chat_with_search(query: str, session_id: Optional[str] = None, num_results: int = 3):
    """
    使用网络搜索增强的对话接口

    - query: 用户问题
    - session_id: 会话ID
    - num_results: 搜索结果数量
    """
    print(f"[DEBUG] /chat_with_search called with query: {query}")
    try:
        # 如果没有提供 session_id，生成一个新的
        if not session_id:
            session_id = str(uuid.uuid4())

        # 创建记忆实例
        memory = create_session_memory(session_id)

        # 创建助手
        assistant = Assistant(memory=memory)

        # 执行网络搜索
        search_context = ""
        if search_tool:
            search_context = search_tool.get_search_context(query, num_results)
            print(f"[DEBUG] Retrieved search context length: {len(search_context)}")

        # 构建增强的查询
        if search_context:
            enhanced_query = f"""基于以下网络搜索结果回答问题：

{search_context}

用户问题：{query}

请基于上述搜索结果回答问题，并提供相关的链接引用。"""
        else:
            enhanced_query = query

        # 处理查询
        response = assistant.chat(enhanced_query)

        return {
            "session_id": session_id,
            "response": response,
            "used_search": bool(search_context)
        }
    except Exception as e:
        print(f"[ERROR] Chat with search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Connection closed")
        await websocket.close()

# ========================================
# 挂载前端静态文件
# ========================================
# 挂载前端目录，使前端可以通过 http://localhost:8000/ 访问
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    print(f"[INFO] Frontend mounted at http://localhost:8000/")
else:
    print(f"[WARNING] Frontend directory not found at {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
