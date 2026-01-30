"""
新增端点说明文档

## 流式输出端点

### GET /agent_chat_stream
流式输出的 Agent 对话接口

参数:
- query: 用户问题
- session_id: 会话ID（可选）

返回: SSE (Server-Sent Events) 流

事件类型:
- metadata: 元数据（tool_used, has_context）
- content: 内容片段
- status: 状态消息
- clear: 清空之前的内容
- done: 完成
- error: 错误

## 文件上传端点

### POST /knowledge/upload_file
上传文件到知识库

参数:
- file: 上传的文件（multipart/form-data）

支持的文件类型:
- PDF (.pdf)
- 文本文件 (.txt, .md)

返回:
{
  "message": "文件已添加到知识库",
  "filename": "example.pdf",
  "chunks_added": 5
}

## 使用示例

### 前端 JavaScript/Vue 示例

```javascript
// 流式输出
const eventSource = new EventSource(`/agent_chat_stream?query=${encodeURIComponent(query)}&session_id=${sessionId}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'metadata':
      console.log('Tool used:', data.tool_used);
      break;
    case 'content':
      // 逐字显示内容
      appendToMessage(data.content);
      break;
    case 'done':
      eventSource.close();
      break;
    case 'error':
      console.error(data.message);
      eventSource.close();
      break;
  }
};

// 文件上传
const formData = new FormData();
formData.append('file', file);

fetch('/knowledge/upload_file', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```
"""
