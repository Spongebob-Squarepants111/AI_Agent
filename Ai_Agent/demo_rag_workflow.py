"""演示 RAG 完整工作流程"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("RAG 工作流程演示")
print("=" * 70)

# 步骤 1: 添加文档（会被向量化）
print("\n【步骤 1】添加文档到知识库（文档会被向量化）")
print("-" * 70)
document = """
脑机接口（Brain-Computer Interface, BCI）是一种直接在大脑和外部设备之间建立通信通道的技术。
BCI 技术的核心原理是通过采集、分析和转换大脑信号来实现人机交互。
目前 BCI 主要分为侵入式和非侵入式两种类型：
- 侵入式 BCI：需要通过手术将电极植入大脑，信号质量高但风险大
- 非侵入式 BCI：通过头皮上的电极采集脑电信号（EEG），安全但信号质量较低
"""

response = requests.post(
    f"{BASE_URL}/knowledge/add_text",
    params={"text": document}
)
print(f"添加结果: {response.json()}")
print("✅ 文档已被分块并向量化存储到 Qdrant")

# 步骤 2: 查看知识库状态
print("\n【步骤 2】查看知识库状态")
print("-" * 70)
response = requests.get(f"{BASE_URL}/knowledge/info")
info = response.json()
print(f"知识库信息:")
print(f"  - 文档数量: {info.get('vectors_count', 0)}")
print(f"  - 存储模式: {info.get('storage_mode', 'unknown')}")

# 步骤 3: 直接搜索（查看检索到的文档片段）
print("\n【步骤 3】向量相似度搜索（查看检索到的文档片段）")
print("-" * 70)
query = "什么是脑机接口？"
print(f"查询: {query}")

response = requests.get(
    f"{BASE_URL}/knowledge/search",
    params={"query": query, "k": 2}
)
search_results = response.json()
print(f"\n检索到 {search_results.get('count', 0)} 个相关文档片段:")
for i, result in enumerate(search_results.get('results', []), 1):
    print(f"\n[文档片段 {i}]")
    print(f"内容: {result['content'][:150]}...")

# 步骤 4: 使用 Agent 对话（完整 RAG 流程）
print("\n【步骤 4】Agent 对话（完整 RAG 流程）")
print("-" * 70)
print(f"问题: {query}")

response = requests.post(
    f"{BASE_URL}/agent_chat",
    params={"query": query}
)
result = response.json()

print(f"\n使用的工具: {result.get('tool_used')}")
print(f"有上下文: {result.get('has_context')}")
print(f"\nLLM 生成的答案:")
print(result.get('response'))

# 总结
print("\n" + "=" * 70)
print("RAG 流程总结")
print("=" * 70)
print("""
1. 文档向量化: 使用 OpenAI Embeddings 将文档转换为向量
2. 向量存储: 存储到 Qdrant 向量数据库
3. 查询向量化: 将用户问题也转换为向量
4. 相似度搜索: 在向量数据库中找到最相关的文档片段
5. 上下文拼接: 将文档片段拼接成上下文
6. Prompt 增强: 将上下文加入系统提示词
7. LLM 生成: GPT 基于上下文生成准确答案
""")
