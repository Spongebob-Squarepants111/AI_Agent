# SSE 到 WebSocket 迁移文档

## 迁移概述

将流式输出从 SSE (Server-Sent Events) 迁移到 WebSocket，实现双向通信和更好的性能。

## 迁移原因

### SSE 的限制
- ❌ 单向通信（仅服务器到客户端）
- ❌ 需要通过 URL 参数传递数据
- ❌ 浏览器连接数限制（HTTP/1.1 每域名 6 个）
- ❌ 不支持二进制数据

### WebSocket 的优势
- ✅ 双向通信（全双工）
- ✅ 通过消息传递数据（更灵活）
- ✅ 更低的延迟
- ✅ 更好的连接管理
- ✅ 支持二进制数据

---

## 后端修改

### 1. 更新导入

**修改前：**
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
```

**修改后：**
```python
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
# 移除 StreamingResponse
```

### 2. 替换 SSE 端点为 WebSocket

**修改前（SSE）：**
```python
@app.get("/agent_chat_stream")
async def agent_chat_stream(query: str, session_id: Optional[str] = None):
    """SSE 端点"""
    async def generate():
        async for chunk in smart_agent.chat_stream(query, memory=langchain_memory):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={...}
    )
```

**修改后（WebSocket）：**
```python
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket.accept()

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            query = data.get("query", "")
            session_id = data.get("session_id")

            # 处理查询并流式发送响应
            async for chunk in smart_agent.chat_stream(query, memory=langchain_memory):
                if chunk.startswith("data: "):
                    chunk_data = json.loads(chunk.replace("data: ", "").strip())
                    await websocket.send_json(chunk_data)

    except WebSocketDisconnect:
        print("[INFO] WebSocket disconnected")
```

### 关键变化
1. **端点类型**：从 `@app.get()` 改为 `@app.websocket()`
2. **URL 路径**：从 `/agent_chat_stream` 改为 `/ws/chat`
3. **数据接收**：从 URL 参数改为 WebSocket 消息
4. **数据发送**：从 `yield` 改为 `await websocket.send_json()`
5. **连接管理**：需要 `accept()` 和处理 `WebSocketDisconnect`

---

## 前端修改

### 1. 替换 EventSource 为 WebSocket

**修改前（SSE）：**
```javascript
async streamChat(query) {
  const url = `${this.apiBaseUrl}/agent_chat_stream?query=${encodeURIComponent(query)}&session_id=${this.sessionId}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // 处理消息
  }

  eventSource.onerror = (error) => {
    eventSource.close()
  }
}
```

**修改后（WebSocket）：**
```javascript
async streamChat(query) {
  const wsUrl = this.apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://')
  const ws = new WebSocket(`${wsUrl}/ws/chat`)

  ws.onopen = () => {
    // 连接成功后发送查询
    ws.send(JSON.stringify({
      query: query,
      session_id: this.sessionId
    }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // 处理消息
  }

  ws.onerror = (error) => {
    ws.close()
  }

  ws.onclose = () => {
    console.log('WebSocket 连接已关闭')
  }
}
```

### 关键变化
1. **协议转换**：`http://` → `ws://`，`https://` → `wss://`
2. **连接方式**：从 `new EventSource(url)` 改为 `new WebSocket(url)`
3. **发送数据**：使用 `ws.send(JSON.stringify(data))` 发送查询
4. **事件处理**：
   - `onopen` - 连接建立时发送查询
   - `onmessage` - 接收消息（与 SSE 类似）
   - `onerror` - 错误处理
   - `onclose` - 连接关闭

---

## 消息格式

### 客户端发送（新增）
```json
{
  "query": "用户问题",
  "session_id": "会话ID（可选）"
}
```

### 服务器响应（保持不变）
```json
// 内容消息
{"type": "content", "content": "文本内容"}

// 完成消息
{"type": "done"}

// 错误消息
{"type": "error", "message": "错误信息"}
```

---

## 测试验证

### 1. WebSocket 测试客户端

创建了 `test_websocket.py` 用于测试：

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "query": "你好",
            "session_id": "test"
        }))

        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data["type"] == "done":
                break
```

### 2. 测试结果

```bash
$ python test_websocket.py

发送消息: {'query': '你好，请介绍一下你自己', 'session_id': 'test_session'}

接收响应:
--------------------------------------------------
 你好！我是一个智能助手，可以帮助你回答各种问题...
--------------------------------------------------
✅ 对话完成
```

### 3. 浏览器测试

打开 `http://localhost:8000/` 测试前端界面：
- ✅ 消息发送正常
- ✅ 流式响应正常
- ✅ 连接管理正常

---

## 对比总结

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| **通信方向** | 单向（服务器→客户端） | 双向（全双工） |
| **协议** | HTTP | WebSocket (ws://) |
| **数据传输** | 文本（SSE 格式） | 文本/二进制 |
| **连接方式** | GET 请求 + 长连接 | 握手升级 |
| **浏览器支持** | 较好 | 优秀 |
| **连接数限制** | 有（HTTP/1.1） | 无 |
| **延迟** | 较低 | 更低 |
| **复杂度** | 简单 | 中等 |

---

## 迁移检查清单

### 后端
- [x] 添加 WebSocket 导入
- [x] 删除 StreamingResponse 导入
- [x] 创建 WebSocket 端点 `/ws/chat`
- [x] 删除 SSE 端点 `/agent_chat_stream`
- [x] 实现消息接收和发送逻辑
- [x] 处理 WebSocketDisconnect 异常

### 前端
- [x] 替换 EventSource 为 WebSocket
- [x] 更新 URL（http → ws）
- [x] 实现 onopen 发送查询
- [x] 更新 onmessage 处理
- [x] 添加 onclose 处理

### 测试
- [x] 创建 WebSocket 测试客户端
- [x] 测试基本对话功能
- [x] 测试流式输出
- [x] 测试错误处理
- [x] 测试连接断开

---

## 优势总结

### 性能提升
- ✅ 更低的延迟（无 HTTP 开销）
- ✅ 更高效的连接管理
- ✅ 支持更多并发连接

### 功能增强
- ✅ 双向通信（未来可扩展）
- ✅ 更灵活的消息格式
- ✅ 更好的错误处理

### 代码质量
- ✅ 更清晰的数据流
- ✅ 更标准的实时通信方式
- ✅ 更易于扩展

---

## 未来扩展

WebSocket 的双向通信特性为未来功能提供了可能：

1. **实时状态更新**
   - 服务器主动推送状态
   - 进度条更新
   - 工具调用通知

2. **中断控制**
   - 客户端可以中断长时间运行的查询
   - 实时取消操作

3. **多轮对话优化**
   - 保持连接进行多轮对话
   - 减少连接建立开销

4. **二进制数据支持**
   - 图片传输
   - 文件上传/下载

---

## 总结

成功将流式输出从 SSE 迁移到 WebSocket：
- ✅ 后端使用 FastAPI WebSocket
- ✅ 前端使用原生 WebSocket API
- ✅ 保持了所有原有功能
- ✅ 提升了性能和可扩展性
- ✅ 通过测试验证

**结论：** WebSocket 提供了更现代、更高效的实时通信方案，为未来功能扩展奠定了基础。
