# AI Agent - 基于 OpenAI + LangChain + RAG 的智能助手

一个功能完整的智能对话助手系统，基于 OpenAI API、LangChain 框架和 RAG（检索增强生成）技术构建。

## 📋 项目简介

本项目提供了一个可扩展的 AI 助手后端服务，支持：
- 🤖 基于 OpenAI GPT 模型的智能对话
- 🧠 RAG 知识库检索增强
- 💾 会话记忆管理
- 📚 多种文档格式支持（URL、PDF、文本）
- 🔍 向量数据库存储与检索
- 🌐 RESTful API 接口

## 🏗️ 技术架构

```
┌─────────────┐
│   客户端     │  (Telegram Bot / 微信 / Web)
└──────┬──────┘
       │ HTTP/WebSocket
┌──────▼──────────────────────────┐
│      FastAPI 服务器              │
├─────────────────────────────────┤
│  LangChain 框架                  │
│  ├─ OpenAI LLM                  │
│  ├─ RAG 检索链                   │
│  ├─ 会话记忆 (Redis)             │
│  └─ 向量存储 (Qdrant)            │
└─────────────────────────────────┘
```

### 核心组件

- **FastAPI**: 高性能 Web 框架，提供 RESTful API
- **LangChain**: AI 应用开发框架，管理 LLM 调用和数据流
- **OpenAI API**: GPT 系列模型，提供强大的语言理解和生成能力
- **Qdrant**: 向量数据库，存储和检索文档嵌入
- **Redis**: 内存数据库，管理会话历史和缓存

## ✨ 主要功能

### 1. 智能对话
- 支持多轮对话，自动维护上下文
- 会话记忆管理，每个用户独立会话
- 流式响应支持（可选）

### 2. RAG 知识库
- 文档向量化存储
- 语义相似度检索
- 上下文增强生成
- 支持多种文档来源：
  - 📄 纯文本
  - 🌐 网页 URL
  - 📑 PDF 文档

### 3. API 接口
- `/chat` - 带记忆的对话接口
- `/simple_chat` - 简单对话接口
- `/add_text` - 添加文本到知识库
- `/add_url` - 从 URL 抓取内容
- `/add_pdf` - 解析 PDF 文档
- `/knowledge/search` - 知识库检索

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Redis 服务器
- Qdrant 向量数据库（可选，用于知识库功能）

### 安装步骤

1. **克隆项目**
```bash
cd /root/Ai_Agent/Ai_Agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**

编辑 `.env` 文件：

```bash
# OpenAI API 配置
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1  # 可选，使用代理时配置

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Qdrant 向量数据库配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# SerpAPI 配置（可选，用于网络搜索）
SERPAPI_KEY=your_serpapi_key_here
```

4. **启动 Redis**
```bash
redis-server
```

5. **启动 Qdrant（可选）**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

6. **启动服务**
```bash
python server.py
```

服务将在 `http://localhost:8000` 启动。

### 验证安装

访问 API 文档：
```
http://localhost:8000/docs
```

## 📖 使用指南

### 1. 简单对话

```python
import requests

response = requests.post(
    "http://localhost:8000/simple_chat",
    params={"query": "你好，请介绍一下人工智能"}
)
print(response.json())
```

### 2. 带会话记忆的对话

```python
import requests

# 第一轮对话
response1 = requests.post(
    "http://localhost:8000/chat",
    params={
        "query": "我想了解机器学习",
        "session_id": "user_001"
    }
)

# 第二轮对话（会记住上下文）
response2 = requests.post(
    "http://localhost:8000/chat",
    params={
        "query": "它有哪些应用场景？",
        "session_id": "user_001"
    }
)
```

### 3. 构建知识库

#### 添加文本
```python
requests.post(
    "http://localhost:8000/add_text",
    params={
        "text": "人工智能（AI）是计算机科学的一个分支...",
        "metadata": '{"source": "manual", "topic": "AI"}'
    }
)
```

#### 从 URL 学习
```python
requests.post(
    "http://localhost:8000/add_url",
    params={"url": "https://example.com/article"}
)
```

#### 从 PDF 学习
```python
requests.post(
    "http://localhost:8000/add_pdf",
    params={"pdf_path": "/path/to/document.pdf"}
)
```

### 4. 检索知识库

```python
response = requests.get(
    "http://localhost:8000/knowledge/search",
    params={"query": "人工智能的应用", "top_k": 5}
)
print(response.json())
```

## 🔧 配置说明

### OpenAI 模型配置

在代码中可以配置使用的模型：

```python
# 推荐模型
- gpt-4-turbo-preview  # 最强性能
- gpt-4                # 平衡性能和成本
- gpt-3.5-turbo        # 快速响应，成本低
```

### RAG 参数调优

```python
# 检索相关文档数量
top_k = 3  # 建议 3-5

# 相似度阈值
similarity_threshold = 0.7  # 0-1 之间

# 文本分块大小
chunk_size = 1000  # 字符数
chunk_overlap = 200  # 重叠字符数
```

## 📁 项目结构

```
Ai_Agent/
├── server.py              # FastAPI 服务器主文件
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量配置
└── README.md             # 项目文档
```

## 🔐 安全建议

1. **保护 API Key**
   - 不要将 `.env` 文件提交到版本控制
   - 定期轮换 API Key
   - 使用环境变量管理敏感信息

2. **访问控制**
   - 在生产环境中添加身份验证
   - 限制 API 调用频率
   - 使用 HTTPS 加密通信

3. **数据安全**
   - 定期备份 Redis 和 Qdrant 数据
   - 对敏感数据进行加密存储
   - 实施数据访问审计

## 🎯 开发路线图

### 当前版本 (v1.0)
- ✅ 基础对话功能
- ✅ RAG 知识库
- ✅ 会话记忆
- ✅ 文档处理

### 计划功能
- [ ] 流式响应支持
- [ ] 多模态输入（图片、音频）
- [ ] 函数调用（Function Calling）
- [ ] Agent 工具链
- [ ] Web UI 界面
- [ ] 用户认证系统
- [ ] 对话历史导出
- [ ] 知识库管理界面

## 🐛 常见问题

### Q: OpenAI API 调用失败？
**A:** 检查以下几点：
1. API Key 是否正确配置
2. 是否有足够的配额
3. 网络连接是否正常（国内可能需要代理）
4. API Base URL 是否正确

### Q: Redis 连接失败？
**A:** 确保 Redis 服务正在运行：
```bash
redis-cli ping  # 应返回 PONG
```

### Q: Qdrant 无法连接？
**A:** 检查 Qdrant 服务状态：
```bash
curl http://localhost:6333/collections
```

### Q: 如何使用代理访问 OpenAI？
**A:** 在 `.env` 中配置：
```bash
# 方式1: 使用代理
HTTP_PROXY=http://your-proxy:port
HTTPS_PROXY=http://your-proxy:port

# 方式2: 使用 API 中转服务
OPENAI_API_BASE=https://your-proxy-api.com/v1
```

## 📚 参考资源

- [OpenAI API 文档](https://platform.openai.com/docs)
- [LangChain 文档](https://python.langchain.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Qdrant 文档](https://qdrant.tech/documentation/)

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开始构建你的 AI 助手吧！** 🚀
