from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import json
import tempfile
import shutil
from typing import Optional
from datetime import datetime
from rag import RAGRetriever
from tools import SearchTool
from agent import LangChainAgent
from memory import create_session_memory, create_langchain_memory, save_conversation_to_redis

# 加载环境变量
load_dotenv()

# ========================================
# FastAPI 应用
# ========================================
app = FastAPI(
    title="BCI Assistant API",
    description="基于 OpenAI 的脑机接口智能助手 API",
    version="1.0.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# 初始化组件
# ========================================
# RAG 检索器
try:
    rag_retriever = RAGRetriever(
        collection_name=os.getenv("QDRANT_COLLECTION", "knowledge_base"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
    )
    print("[INFO] RAG retriever initialized successfully")
except Exception as e:
    print(f"[WARNING] RAG retriever initialization failed: {e}")
    rag_retriever = None

# 搜索工具
try:
    search_tool = SearchTool(api_key=os.getenv("SERPAPI_KEY"))
    print("[INFO] Search tool initialized successfully")
except Exception as e:
    print(f"[WARNING] Search tool initialization failed: {e}")
    search_tool = None

# 智能 Agent
smart_agent = None
try:
    smart_agent = LangChainAgent(rag_retriever=rag_retriever, search_tool=search_tool)
    print("[INFO] LangChain Agent initialized successfully")
except Exception as e:
    print(f"[WARNING] LangChain Agent initialization failed: {e}")

# ========================================
# API 端点
# ========================================
@app.get("/api")
def read_root():
    """API 根路径"""
    return {
        "message": "Welcome to BCI Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }

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

    # 生成 session_id
    if not session_id:
        session_id = f"session_{int(datetime.now().timestamp() * 1000)}"

    # 创建 Redis 记忆实例
    redis_memory = create_session_memory(session_id)

    # 创建 LangChain Memory（从 Redis 加载历史）
    langchain_memory = create_langchain_memory(redis_memory)

    async def generate():
        try:
            full_response = ""
            async for chunk in smart_agent.chat_stream(query, memory=langchain_memory):
                # 收集完整回答
                if '"type": "content"' in chunk:
                    data = json.loads(chunk.replace("data: ", "").strip())
                    if data.get("type") == "content":
                        full_response += data.get("content", "")

                yield chunk

            # 保存对话到 Redis
            if full_response:
                save_conversation_to_redis(redis_memory, query, full_response)

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

@app.post("/knowledge/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文件到知识库

    支持格式: PDF, TXT, MD
    """
    if not rag_retriever:
        return {"error": "RAG功能未启用"}

    try:
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

@app.get("/knowledge/info")
def get_knowledge_info():
    """获取知识库信息（用于调试）"""
    if not rag_retriever:
        return {"error": "RAG功能未启用"}

    try:
        info = rag_retriever.get_collection_info()
        return info
    except Exception as e:
        return {"error": str(e)}

# ========================================
# 挂载前端静态文件
# ========================================
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    print(f"[INFO] Frontend mounted at http://localhost:8000/")
else:
    print(f"[WARNING] Frontend directory not found at {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
