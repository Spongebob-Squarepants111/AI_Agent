"""演示 AI 不知道时触发搜索的功能"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("演示：AI 不知道时自动触发搜索")
print("=" * 70)

# 确保知识库为空
print("\n【步骤 1】检查知识库状态")
print("-" * 70)
response = requests.get(f"{BASE_URL}/knowledge/info")
info = response.json()
print(f"知识库状态: {json.dumps(info, indent=2, ensure_ascii=False)}")
print(f"文档数量: {info.get('vectors_count', 0)}")

# 测试：询问 AI 不知道的问题
print("\n【步骤 2】询问 AI 不知道的问题")
print("-" * 70)
query = "2026年1月29日有什么重要新闻？"
print(f"问题: {query}")

response = requests.post(
    f"{BASE_URL}/agent_chat",
    params={"query": query}
)
result = response.json()

print(f"\n使用的工具: {result.get('tool_used')}")
print(f"有上下文: {result.get('has_context')}")
print(f"\nAI 回答:")
print(result.get('response'))

# 分析结果
print("\n" + "=" * 70)
print("结果分析:")
print("=" * 70)
if result.get('tool_used') == 'search':
    print("✅ 成功！AI 检测到不知道答案，自动触发了搜索")
elif result.get('tool_used') == 'none':
    print("⚠️  AI 直接回答了，没有触发搜索")
    print("   可能原因：AI 的回答中没有包含'不知道'等关键词")
else:
    print(f"❓ 使用了其他工具: {result.get('tool_used')}")

print("\n触发搜索的条件:")
print("1. 知识库为空（无文档）")
print("2. AI 的回答包含'不知道'、'无法回答'、'无法提供'等关键词")
print("3. SerpAPI 搜索工具可用")
