"""测试新的 Agent 决策逻辑"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("测试新的 Agent 决策逻辑")
print("=" * 70)

# 测试 1: 知识库为空时，一般性问题
print("\n【测试 1】知识库为空 - 一般性问题")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/agent_chat",
    params={"query": "你好，你是谁？"}
)
result = response.json()
print(f"问题: 你好，你是谁？")
print(f"使用的工具: {result.get('tool_used')}")
print(f"回答: {result.get('response')[:100]}...\n")

# 测试 2: 知识库为空时，AI 不知道的问题
print("\n【测试 2】知识库为空 - AI 不知道的问题（应该触发搜索）")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/agent_chat",
    params={"query": "2026年1月29日的最新新闻是什么？"}
)
result = response.json()
print(f"问题: 2026年1月29日的最新新闻是什么？")
print(f"使用的工具: {result.get('tool_used')}")
print(f"回答: {result.get('response')[:200]}...\n")

# 测试 3: 添加文档到知识库
print("\n【测试 3】添加文档到知识库")
print("-" * 70)
knowledge_text = """
脑机接口（Brain-Computer Interface, BCI）是一种直接在大脑和外部设备之间建立通信通道的技术。
BCI 技术可以帮助残障人士控制假肢、轮椅等设备，也可以用于游戏、虚拟现实等领域。
目前 BCI 技术主要分为侵入式和非侵入式两种类型。
侵入式 BCI 需要通过手术将电极植入大脑，而非侵入式 BCI 则通过头皮上的电极采集脑电信号。
"""
response = requests.post(
    f"{BASE_URL}/knowledge/add_text",
    params={"text": knowledge_text}
)
print(f"添加结果: {response.json()}\n")

# 测试 4: 有文档后，询问知识库中的内容
print("\n【测试 4】有文档后 - 询问知识库内容（应该使用 RAG）")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/agent_chat",
    params={"query": "什么是脑机接口？"}
)
result = response.json()
print(f"问题: 什么是脑机接口？")
print(f"使用的工具: {result.get('tool_used')}")
print(f"有上下文: {result.get('has_context')}")
print(f"回答: {result.get('response')}\n")

# 测试 5: 有文档后，询问知识库外的内容
print("\n【测试 5】有文档后 - 询问知识库外的内容")
print("-" * 70)
response = requests.post(
    f"{BASE_URL}/agent_chat",
    params={"query": "Python 是什么编程语言？"}
)
result = response.json()
print(f"问题: Python 是什么编程语言？")
print(f"使用的工具: {result.get('tool_used')}")
print(f"有上下文: {result.get('has_context')}")
print(f"回答: {result.get('response')[:200]}...\n")

print("=" * 70)
print("测试完成！")
print("=" * 70)
