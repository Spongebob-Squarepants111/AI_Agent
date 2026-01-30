"""测试搜索功能的示例脚本"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_search():
    """测试网络搜索接口"""
    print("=" * 50)
    print("测试网络搜索接口")
    print("=" * 50)

    # 测试搜索
    query = "Python programming language"
    response = requests.get(
        f"{BASE_URL}/search",
        params={"query": query, "num_results": 3}
    )

    print(f"\n查询: {query}")
    print(f"状态码: {response.status_code}")
    print(f"\n结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_chat_with_search():
    """测试带搜索的对话接口"""
    print("\n" + "=" * 50)
    print("测试带搜索的对话接口")
    print("=" * 50)

    query = "What are the latest features in Python 3.12?"
    response = requests.post(
        f"{BASE_URL}/chat_with_search",
        params={"query": query, "num_results": 3}
    )

    print(f"\n问题: {query}")
    print(f"状态码: {response.status_code}")
    print(f"\n回答:")
    result = response.json()
    print(f"Session ID: {result.get('session_id')}")
    print(f"Used Search: {result.get('used_search')}")
    print(f"Response: {result.get('response')}")

if __name__ == "__main__":
    print("注意: 请确保已在 .env 文件中配置 SERPAPI_KEY")
    print("注意: 请确保服务器正在运行 (python server.py)")
    print()

    try:
        # 测试基本搜索
        test_search()

        # 测试带搜索的对话
        test_chat_with_search()

    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"\n错误: {str(e)}")
