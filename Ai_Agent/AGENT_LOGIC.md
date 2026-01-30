# Agent 决策逻辑优化说明

## 新的决策逻辑

根据您的需求，Agent 现在采用以下智能决策逻辑：

### 决策流程

```
用户提问
    ↓
检查知识库是否有文档？
    ↓
有文档 → 使用 RAG 知识增强
    ↓
没有文档 → 直接回答
    ↓
AI 表示不知道？
    ↓
是 → 调用 SerpAPI 搜索
    ↓
否 → 返回回答
```

### 核心特点

1. **基于文档存在性判断**
   - 不再依赖关键词匹配
   - 检查知识库中是否有向量（vectors_count > 0）
   - 更准确、更可靠

2. **智能回退机制**
   - 有文档：优先使用 RAG
   - 无文档：直接回答
   - 不知道：自动搜索

3. **用户体验优化**
   - 用户上传文档后，所有问题都会基于文档回答
   - 避免了关键词匹配的不准确性
   - 更符合实际使用场景

## 测试结果

### 测试 1：知识库为空 - 一般性问题
- **问题**：你好，你是谁？
- **工具**：none
- **结果**：✅ 直接回答

### 测试 2：知识库为空 - 不知道的问题
- **问题**：2026年1月29日的最新新闻是什么？
- **工具**：search（如果 AI 表示不知道）
- **结果**：✅ 触发搜索

### 测试 3：有文档 - 询问知识库内容
- **问题**：什么是脑机接口？
- **工具**：knowledge
- **结果**：✅ 使用 RAG，基于文档回答

### 测试 4：有文档 - 询问知识库外内容
- **问题**：Python 是什么编程语言？
- **工具**：knowledge
- **结果**：✅ 仍使用 RAG（符合设计：上传文档后优先使用文档）

## 使用方法

### API 调用

```bash
# Agent 智能对话
curl -X POST "http://localhost:8000/agent_chat?query=你的问题"
```

### Python 调用

```python
import requests

response = requests.post(
    "http://localhost:8000/agent_chat",
    params={"query": "什么是脑机接口？"}
)
result = response.json()

print(f"回答: {result['response']}")
print(f"使用的工具: {result['tool_used']}")  # "knowledge" | "search" | "none"
print(f"有上下文: {result['has_context']}")
```

## 优势

1. **更智能**：基于实际状态（是否有文档）而非关键词
2. **更准确**：避免关键词匹配的误判
3. **更灵活**：自动回退到搜索
4. **更符合直觉**：上传文档就用文档，没文档就直接答或搜索

## 实现文件

- `agent/smart_agent.py` - 核心决策逻辑
- `server.py` - API 端点
- `test_new_agent_logic.py` - 测试脚本
