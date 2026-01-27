from fastapi import FastAPI,WebSocket,WebSocketDisconnect, Query
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import PromptTemplate,MessagesPlaceholder
from langchain.agents import create_react_agent,AgentExecutor,tool
from langchain import hub
from dotenv import load_dotenv
import os
import redis
import json
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import asyncio

# 导入新增模块
from config.personality import PERSONALITY
from rag.retriever import knowledge_retriever
from emotion.analyzer import emotion_analyzer
from tts.synthesizer import tts_synthesizer
from memory.short_term import create_session_memory, ChatMemory
from tools.rag_tool import rag_tools
from tools.search import search_tools


# 包装 ChatTongyi 以强制禁用流式输出
class NonStreamingChatTongyi(ChatTongyi):
    """重写 ChatTongyi，强制禁用流式输出，改用 invoke"""
    def _stream(self, *args, **kwargs):
        # 禁用流式，改用 invoke
        result = self.invoke(*args, **kwargs)
        yield result
    
    def stream(self, *args, **kwargs):
        # 禁用流式，改用 invoke
        result = self.invoke(*args, **kwargs)
        yield result

# 加载 .env 文件中的环境变量
load_dotenv()

# 合并所有工具
all_tools = []
all_tools.extend(rag_tools)
all_tools.extend(search_tools)

# 添加一个测试工具
@tool
def test():
    """Test tool"""
    return f"Test"    

class Agent:
    def __init__(self, memory: Optional[ChatMemory] = None):
        # 使用配置的性格系统提示
        system_prompt = PERSONALITY["system_prompt"].format(
            personality_name=PERSONALITY["name"],
            personality_traits=",".join(PERSONALITY["traits"]),
            speaking_style=PERSONALITY["speaking_style"]
        )
        
        self.chat_model = NonStreamingChatTongyi(
            model="qwen-turbo",  # 使用通义千问 turbo 模型（免费）
            temperature=0,
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
        self.memory = memory
        
        # 合并所有工具
        tools = []
        tools.extend(all_tools)
        tools.append(test)
        
        # 使用 ReAct Agent，更适合通义千问
        react_prompt = PromptTemplate.from_template(system_prompt + "\n{chat_history}\n\n你可以使用以下工具：\n{tools}\n\n工具名称：{tool_names}\n\n当需要使用工具时，你必须按照以下格式回答：\nThought: 你对当前问题的思考\nAction: 工具名称\nAction Input: 工具的输入\nObservation: 工具的返回结果\n... (可以重复 Thought/Action/Action Input/Observation 多次)\nThought: 我现在知道最终答案\nFinal Answer: 给用户的最终回答\n\n当不需要工具时，直接回答：\nThought: 我可以直接回答这个问题\nFinal Answer: 你的答案\n\n开始！\n\n用户问题: {input}\n\n{agent_scratchpad}")
        
        agent = create_react_agent(
            tools=tools,
            llm=self.chat_model,
            prompt=react_prompt,
        )
        self.agent_excutor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True,  # 自动处理解析错误
        )

    def run(self, query: str, emotion_analysis: Dict = None):
        print(f"[DEBUG] Received query: {query}")
        try:
            # 获取历史记录
            chat_history = ""
            if self.memory:
                chat_history = self.memory.get_history_string()
            
            # 如果进行了情绪分析，将情绪反馈加入到上下文中
            if emotion_analysis and emotion_analysis.get("should_adjust_tone"):
                emotion_feedback = f"\n[情绪分析] 用户当前情绪: {emotion_analysis['detected_emotion']} (置信度: {emotion_analysis['confidence']:.2f})\n情绪回应: {emotion_analysis['emotion_response']}\n"
                chat_history += emotion_feedback
            
            result = self.agent_excutor.invoke({
                "input": query,
                "chat_history": chat_history
            })
            print(f"[DEBUG] Result: {result}")
            
            # 保存对话到记忆
            if self.memory:
                self.memory.add_message("user", query)
                output = result.get("output", str(result))
                self.memory.add_message("assistant", output)
            
            return result
        except Exception as e:
            print(f"[ERROR] Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}


app = FastAPI()
@app.get("/")
def read_root():
    return {"Hello": "World"}

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
        
        # 进行情绪分析
        emotion_analysis = emotion_analyzer.analyze_and_respond(query)
        
        master = Agent(memory=memory)
        print("[DEBUG] Agent initialized with memory")
        result = master.run(query, emotion_analysis=emotion_analysis)
        
        # 返回结果时包含 session_id
        response = {
            "session_id": session_id,
            "output": result.get("output", str(result)) if isinstance(result, dict) else str(result),
            "emotion_analysis": emotion_analysis
        }
        print(f"[DEBUG] Returning result: {response}")
        return response
    except Exception as e:
        print(f"[ERROR] Chat endpoint error: {str(e)}")
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

@app.post("/simple_chat")
def simple_chat(query: str):
    """简单的聊天接口，不使用 Agent，直接调用通义千问"""
    print(f"[DEBUG] /simple_chat endpoint called with query: {query}")
    try:
        from langchain_community.chat_models import ChatTongyi
        chat_model = ChatTongyi(
            model="qwen-turbo",
            temperature=0,
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
        print("[DEBUG] Sending request to Tongyi...")
        response = chat_model.invoke(query)
        print(f"[DEBUG] Tongyi response received: {response.content}")
        return {"response": response.content}
    except Exception as e:
        print(f"[ERROR] Simple chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/add_url")
async def add_url(url: str, metadata: Dict = {}):
    """添加网页内容到知识库"""
    try:
        # 这里应该实现网页抓取和解析逻辑
        # 暂时使用模拟数据
        content = f"网页内容来自: {url} (实际应用中应实现网页抓取和解析)"
        doc_id = knowledge_retriever.add_knowledge(content, metadata)
        return {"doc_id": doc_id, "url": url, "message": "URL content added to knowledge base"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/add_pdf")
async def add_pdf(pdf_path: str, metadata: Dict = {}):
    """添加PDF内容到知识库"""
    try:
        # 这里应该实现PDF解析逻辑
        # 暂时使用模拟数据
        content = f"PDF内容来自: {pdf_path} (实际应用中应实现PDF解析)"
        doc_id = knowledge_retriever.add_knowledge(content, metadata)
        return {"doc_id": doc_id, "pdf_path": pdf_path, "message": "PDF content added to knowledge base"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/add_text")
async def add_text(text: str, metadata: Dict = {}):
    """添加文本内容到知识库"""
    try:
        doc_id = knowledge_retriever.add_knowledge(text, metadata)
        return {"doc_id": doc_id, "message": "Text content added to knowledge base"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/knowledge/search")
def search_knowledge(query: str, top_k: int = 3):
    """搜索知识库"""
    try:
        results = knowledge_retriever.retrieve(query, top_k=top_k)
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/knowledge/{doc_id}")
def delete_knowledge(doc_id: str):
    """删除知识库中的文档"""
    try:
        success = knowledge_retriever.delete_knowledge(doc_id)
        if success:
            return {"message": f"Document {doc_id} deleted from knowledge base"}
        else:
            return {"error": "Failed to delete document"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/tts/synthesize")
async def synthesize_text(text: str, voice: str = "zh-CN-XiaoxiaoNeural", rate: str = "+0%", volume: str = "+0%"):
    """文本转语音接口"""
    try:
        filepath = tts_synthesizer.synthesize(text, voice, rate, volume)
        return {"audio_file": filepath, "message": "TTS synthesis completed"}
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Connection closed")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)