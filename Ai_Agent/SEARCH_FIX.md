# 搜索功能修复说明

## 🐛 问题描述

当用户进行多轮对话时，如果用户的回复很简短（如"需要"、"是的"），系统会错误地使用这个简短回复作为搜索查询，而不是使用原始问题。

### 问题示例

**对话流程：**
1. 用户: "今天重庆温度怎么样"
2. AI: "我可以帮您查找实时天气信息，需要吗？"
3. 用户: "需要"
4. 系统: ❌ 搜索 "需要" → 得到无关结果

**期望行为：**
- 系统应该搜索 "今天重庆温度怎么样" 或 "重庆今天天气"

## 🔧 修复方案

在 `SmartAgent` 类中添加了 `_generate_search_query()` 方法，智能地从对话历史中提取真实的搜索意图。

### 核心逻辑

```python
def _generate_search_query(self, query: str, chat_history: list = None) -> str:
    """
    基于当前查询和对话历史生成更好的搜索查询

    如果当前查询很短（≤5个字符），从历史中找到最近的用户问题
    """
    if len(query) <= 5 and chat_history:
        # 从历史中找到最近的用户问题
        for msg in reversed(chat_history):
            if hasattr(msg, 'type') and msg.type == 'human' and len(msg.content) > 5:
                return msg.content

    return query
```

### 修改的文件

**agent/smart_agent.py**
- 新增 `_generate_search_query()` 方法（第 93-112 行）
- 更新 `chat()` 方法中的搜索调用（第 184-186 行）
- 更新 `chat_stream()` 方法中的搜索调用（第 287-289 行）

## ✅ 修复效果

### 修复前
```
[DEBUG] /agent_chat_stream called with query: 需要
[INFO] AI doesn't know, using web search
[INFO] Found 3 search results for query: 需要  ❌ 错误的搜索查询
```

### 修复后
```
[DEBUG] /agent_chat_stream called with query: 需要
[INFO] AI doesn't know, using web search
[DEBUG] Using previous user query for search: 今天重庆温度怎么样  ✅ 从历史中提取
[DEBUG] Generated search query: 今天重庆温度怎么样
[INFO] Found 3 search results for query: 今天重庆温度怎么样  ✅ 正确的搜索查询
```

## 🧪 测试场景

### 场景 1: 简短回复触发搜索
```
用户: "今天重庆温度怎么样"
AI: "我可以帮您查找，需要吗？"
用户: "需要"  ← 触发搜索
系统: ✅ 搜索 "今天重庆温度怎么样"
```

### 场景 2: 直接问题触发搜索
```
用户: "2024年诺贝尔物理学奖得主是谁"
AI: "抱歉，我不知道..."
系统: ✅ 搜索 "2024年诺贝尔物理学奖得主是谁"
```

### 场景 3: 长回复不受影响
```
用户: "请帮我搜索一下重庆今天的天气情况"
AI: "抱歉，我无法获取实时天气..."
系统: ✅ 搜索 "请帮我搜索一下重庆今天的天气情况"
```

## 📝 技术细节

### 判断逻辑
- **短查询阈值**: ≤5 个字符
- **历史查询阈值**: >5 个字符
- **消息类型**: 只查找 `human` 类型的消息（用户消息）

### 为什么选择 5 个字符？
- 中文: "需要"(2字)、"是的"(2字)、"好的"(2字)、"可以"(2字)
- 英文: "yes"(3字)、"ok"(2字)、"sure"(4字)
- 5 个字符可以覆盖大部分简短回复，同时避免误判正常问题

## 🎯 后续优化建议

### 1. 使用 LLM 生成搜索查询
```python
def _generate_search_query_with_llm(self, query: str, chat_history: list) -> str:
    """使用 LLM 理解对话上下文，生成最佳搜索查询"""
    prompt = f"基于以下对话，生成一个最佳的搜索查询：\n{chat_history}\n当前问题：{query}"
    # 调用 LLM 生成搜索查询
```

### 2. 支持多语言
- 当前只考虑了中文和英文
- 可以添加其他语言的简短回复检测

### 3. 更智能的意图识别
- 识别"换个话题"、"不需要了"等否定回复
- 避免在用户不需要时触发搜索

## 📊 性能影响

- **额外开销**: 遍历对话历史（通常 <10 条消息）
- **时间复杂度**: O(n)，n 为历史消息数量
- **影响**: 可忽略不计（<1ms）

## ✅ 验证清单

- [x] 语法检查通过
- [x] 短查询能正确提取历史问题
- [x] 长查询不受影响
- [x] 无对话历史时不会崩溃
- [x] 代码注释清晰
- [x] 调试日志完整

---

**修复时间**: 2026-01-30
**修复文件**: agent/smart_agent.py
**影响范围**: 搜索功能的查询生成逻辑
