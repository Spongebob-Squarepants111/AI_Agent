#!/bin/bash
# SerpAPI 功能测试脚本

echo "=========================================="
echo "测试 1: 直接搜索接口"
echo "=========================================="
curl -X GET "http://localhost:8000/search?query=Python编程语言&num_results=3" \
  -H "Content-Type: application/json" | python -m json.tool

echo -e "\n\n=========================================="
echo "测试 2: 带搜索的对话接口"
echo "=========================================="
curl -X POST "http://localhost:8000/chat_with_search?query=Python%203.12有哪些新特性&num_results=3" \
  -H "Content-Type: application/json" | python -m json.tool

echo -e "\n\n测试完成！"
