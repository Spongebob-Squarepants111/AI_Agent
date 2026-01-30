"""测试 _check_if_unknown 方法"""

# 模拟不同的 LLM 回答
test_responses = [
    # 应该触发搜索的回答
    ("抱歉，我目前无法实时获取天气信息。", True),
    ("我不知道2024年诺贝尔奖得主是谁。", True),
    ("很遗憾，我无法提供最新的股价信息。", True),
    ("对不起，我无法访问实时数据。", True),
    ("I don't know the current weather.", True),
    ("Sorry, I cannot access real-time information.", True),
    ("Unfortunately, I'm unable to provide that information.", True),

    # 不应该触发搜索的回答
    ("北京今天天气晴朗，温度15度。", False),
    ("根据我的知识，脑机接口是一种技术。", False),
    ("我可以帮你解答这个问题。", False),
    ("这是一个很好的问题，让我来回答。", False),
]

print("=" * 70)
print("测试 _check_if_unknown 方法")
print("=" * 70)

# 导入必要的模块
import sys
sys.path.insert(0, '/root/Ai_Agent/Ai_Agent')

from agent.smart_agent import SmartAgent

# 创建 SmartAgent 实例（不需要实际的工具）
agent = SmartAgent()

print("\n测试结果：\n")
all_passed = True

for response, expected in test_responses:
    result = agent._check_if_unknown(response)
    status = "✅ PASS" if result == expected else "❌ FAIL"

    if result != expected:
        all_passed = False

    print(f"{status} | 预期: {expected:5} | 实际: {result:5} | 回答: {response[:50]}...")

print("\n" + "=" * 70)
if all_passed:
    print("✅ 所有测试通过！")
else:
    print("❌ 部分测试失败，请检查关键词列表")
print("=" * 70)
