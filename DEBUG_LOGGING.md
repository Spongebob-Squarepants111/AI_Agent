# LLM Debug 日志说明

## 📝 新增功能

在 SmartAgent 中添加了 LLM 返回信息的 debug 日志，方便在后端查看 LLM 的完整响应内容。

## 🔍 Debug 日志位置

### 1. 非流式输出 (`chat()` 方法)

**初始回答**：
```python
[DEBUG] LLM initial response: <完整的 LLM 回答>
```
- 位置：`smart_agent.py:131`
- 触发时机：LLM 首次回答用户问题后

**搜索后回答**：
```python
[DEBUG] LLM response after search: <基于搜索结果的回答>
```
- 位置：`smart_agent.py:155`
- 触发时机：当 AI 表示不知道，触发搜索后重新回答

### 2. 流式输出 (`chat_stream()` 方法)

**流式回答**：
```python
[DEBUG] LLM stream response: <完整的流式回答>
```
- 位置：`smart_agent.py:228`
- 触发时机：流式输出完成后，打印完整内容

**搜索后流式回答**：
```python
[DEBUG] LLM response after search: <基于搜索结果的流式回答>
```
- 位置：`smart_agent.py:262`
- 触发时机：触发搜索后，流式输出完成

## 📊 日志示例

### 示例 1：使用 RAG 的回答

```
[INFO] Knowledge base has 5 vectors
[INFO] Knowledge base has documents, using RAG
[INFO] Retrieved context from knowledge base
[DEBUG] LLM stream response: 脑机接口（BCI）是一种直接在大脑和外部设备之间建立通信通道的技术...
```

### 示例 2：触发搜索的回答

```
[INFO] Knowledge base has 0 vectors
[DEBUG] LLM stream response: 抱歉，我不知道2024年诺贝尔物理学奖得主是谁。
[INFO] AI doesn't know, using web search
[INFO] Searching for: 2024年诺贝尔物理学奖得主是谁？
[INFO] Found 3 search results
[DEBUG] LLM response after search: 根据搜索结果，2024年诺贝尔物理学奖授予了...
```

### 示例 3：直接回答

```
[INFO] Knowledge base has 0 vectors
[DEBUG] LLM stream response: 你好！我是 BCI 智能助手，很高兴为你服务...
```

## 🎯 使用场景

### 1. 调试问题
当用户反馈 AI 回答不准确时，可以通过 debug 日志查看：
- LLM 实际返回了什么内容
- 是否正确使用了知识库或搜索结果
- 回答是否被正确传递到前端

### 2. 监控质量
- 检查 LLM 的回答质量
- 验证 RAG 是否有效
- 确认搜索结果是否被正确使用

### 3. 追踪决策
结合其他日志，可以完整追踪 Agent 的决策过程：
```
[INFO] Knowledge base has 5 vectors          # 知识库状态
[INFO] Knowledge base has documents, using RAG  # 决策：使用 RAG
[INFO] Retrieved context from knowledge base    # 检索到上下文
[DEBUG] LLM stream response: ...               # LLM 的完整回答
```

## 🔧 如何查看日志

### 方法 1：直接在终端查看
运行服务器时，日志会直接输出到终端：
```bash
cd /root/Ai_Agent/Ai_Agent
python server.py
```

### 方法 2：重定向到文件
将日志保存到文件以便后续分析：
```bash
python server.py 2>&1 | tee server.log
```

### 方法 3：只查看 DEBUG 日志
使用 grep 过滤：
```bash
python server.py 2>&1 | grep "\[DEBUG\]"
```

## 📋 完整日志层级

```
[DEBUG]   - LLM 返回的完整内容（新增）
[INFO]    - 一般信息（知识库状态、工具使用等）
[WARNING] - 警告信息（搜索失败、知识库检查失败等）
[ERROR]   - 错误信息（LLM 调用失败、流式输出失败等）
```

## 💡 提示

1. **生产环境**：可以通过环境变量控制是否显示 DEBUG 日志
2. **性能影响**：DEBUG 日志对性能影响很小，可以放心使用
3. **隐私考虑**：日志中包含用户问题和 AI 回答，注意保护用户隐私
4. **日志轮转**：长期运行建议配置日志轮转，避免日志文件过大

## 🔄 后续优化建议

1. 添加日志级别控制（通过环境变量）
2. 添加时间戳和请求 ID
3. 将日志输出到文件而不是终端
4. 集成日志分析工具（如 ELK）
