# Agent 搜索触发机制说明

## 🔍 问题分析

### 原始问题
用户问"今天北京天气怎么样"，LLM 回答：
```
抱歉，我目前无法实时获取天气信息。不过你可以通过手机上的天气应用或者搜索引擎查看北京的最新天气预报。
```

这个回答明显表示 AI 不知道答案，但是**没有触发 SerpAPI 搜索**。

### 根本原因
`_check_if_unknown()` 方法中的关键词列表不够完善，无法识别"无法实时获取"这种表达方式。

## ✅ 解决方案

### 扩展的关键词列表

现在包含以下类型的关键词：

#### 1. 中文 - 直接表示不知道
- 不知道、不清楚、不了解、不确定

#### 2. 中文 - 无法提供/回答
- 无法回答、无法提供、无法查询、**无法获取**、无法访问
- **无法实时**、无法直接、无法确定

#### 3. 中文 - 没有信息
- 没有信息、没有数据、没有相关

#### 4. 中文 - 抱歉/遗憾
- **抱歉**、很遗憾、对不起

#### 5. 英文关键词
- don't know, cannot answer, unable to provide
- **sorry**, apologize, unfortunately
- cannot get, cannot access, unable to get

### 新增的 Debug 功能

当检测到"不知道"时，会打印匹配的关键词：
```python
[DEBUG] Detected 'unknown' response, matched keywords: ['抱歉', '无法实时', '无法获取']
```

## 🧪 测试

运行测试脚本验证：
```bash
cd /root/Ai_Agent
/root/anaconda3/envs/agent/bin/python test_check_unknown.py
```

## 📊 预期效果

### 修改前
```
[INFO] Knowledge base has 0 vectors
[DEBUG] LLM stream response: 抱歉，我目前无法实时获取天气信息...
# 没有触发搜索
```

### 修改后
```
[INFO] Knowledge base has 0 vectors
[DEBUG] LLM stream response: 抱歉，我目前无法实时获取天气信息...
[DEBUG] Detected 'unknown' response, matched keywords: ['抱歉', '无法实时', '无法获取']
[INFO] AI doesn't know, using web search
[INFO] Searching for: 今天北京天气怎么样
[INFO] Found 3 search results
[DEBUG] LLM response after search: 根据搜索结果，北京今天...
```

## 🎯 触发搜索的条件

Agent 会在以下情况触发 SerpAPI 搜索：

1. ✅ **知识库为空**（`vectors_count == 0`）
2. ✅ **LLM 表示不知道**（匹配关键词列表）
3. ✅ **搜索工具可用**（`search_tool` 已初始化）

## 💡 常见的"不知道"表达

### 会触发搜索的回答
- "抱歉，我无法实时获取..."
- "很遗憾，我不知道..."
- "对不起，我无法提供..."
- "我目前无法访问..."
- "Sorry, I cannot access..."
- "Unfortunately, I don't have..."

### 不会触发搜索的回答
- "根据我的知识，..."
- "这是一个很好的问题，..."
- "让我来回答你的问题..."
- "我可以帮你..."

## 🔧 如何测试

### 1. 重启服务器
```bash
cd /root/Ai_Agent/Ai_Agent
python server.py
```

### 2. 在前端测试
访问 http://localhost:8000/，问以下问题：
- "今天北京天气怎么样？"
- "2024年诺贝尔物理学奖得主是谁？"
- "特斯拉最新的股价是多少？"

### 3. 观察后端日志
应该看到：
```
[DEBUG] LLM stream response: 抱歉，我目前无法...
[DEBUG] Detected 'unknown' response, matched keywords: ['抱歉', '无法实时']
[INFO] AI doesn't know, using web search
```

## 📝 注意事项

1. **关键词匹配是模糊的**：只要回答中包含任何一个关键词就会触发
2. **可能的误触发**：如果 LLM 在正常回答中使用了"抱歉"等词，也可能触发搜索
3. **持续优化**：可以根据实际使用情况继续调整关键词列表

## 🚀 后续优化建议

1. **使用 LLM 判断**：让另一个 LLM 判断回答是否表示"不知道"
2. **置信度评分**：根据匹配的关键词数量计算置信度
3. **上下文分析**：考虑整个对话的上下文，而不仅仅是单个回答
4. **用户反馈**：允许用户手动触发搜索
