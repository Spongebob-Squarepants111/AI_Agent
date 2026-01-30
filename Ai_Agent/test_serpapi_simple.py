"""简单的 SerpAPI 搜索测试脚本"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("SerpAPI 搜索功能测试")
print("=" * 60)

# 测试 1: 直接搜索
print("\n【测试 1】直接搜索接口")
print("-" * 60)
response = requests.get(
    f"{BASE_URL}/search",
    params={"query": "Python programming", "num_results": 2}
)
print(f"状态码: {response.status_code}")
print(f"结果:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")

# 测试 2: 带搜索的对话
print("\n【测试 2】带搜索的对话接口")
print("-" * 60)
response = requests.post(
    f"{BASE_URL}/chat_with_search",
    params={"query": "What are the main features of Python?", "num_results": 2}
)
print(f"状态码: {response.status_code}")
result = response.json()
print(f"Session ID: {result.get('session_id')}")
print(f"使用了搜索: {result.get('used_search')}")
print(f"AI 回答:\n{result.get('response')}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
