#!/bin/bash
# DeepSeek 流式输出测试脚本
# 用于测试 FastAPI /chat/stream 接口的流式输出

BASE_URL="http://localhost:8000"
ENDPOINT="${BASE_URL}/chat/stream"

echo "=========================================="
echo "DeepSeek 流式输出测试"
echo "=========================================="
echo ""

# 测试 1: 基本流式输出（自动创建会话）
echo "【测试 1】基本流式输出（自动创建会话）"
echo "----------------------------------------"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "什么是系统科学？",
    "session_id": null
  }' \
  --no-buffer \
  -N \
  -s

echo ""
echo ""
echo "=========================================="
echo ""

# 测试 2: 格式化输出（使用 jq，如果可用）
if command -v jq &> /dev/null; then
    echo "【测试 2】格式化流式输出（使用 jq）"
    echo "----------------------------------------"
    curl -X POST "${ENDPOINT}" \
      -H "Content-Type: application/json" \
      -d '{
        "message": "请简要介绍系统科学的核心概念",
        "session_id": null
      }' \
      --no-buffer \
      -N \
      -s | while IFS= read -r line; do
        if [[ $line == data:* ]]; then
            # 提取 JSON 数据
            json_data="${line#data: }"
            echo "$json_data" | jq -c '.'
        fi
    done
else
    echo "【测试 2】跳过（需要安装 jq: sudo apt-get install jq 或 brew install jq）"
fi

echo ""
echo ""
echo "=========================================="
echo ""

# 测试 3: 详细输出（显示所有事件类型）
echo "【测试 3】详细流式输出（显示事件类型）"
echo "----------------------------------------"
curl -X POST "${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "系统科学有哪些主要应用领域？",
    "session_id": null
  }' \
  --no-buffer \
  -N \
  -s | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
        # 提取 JSON 数据
        json_data="${line#data: }"
        # 解析并显示
        chunk_type=$(echo "$json_data" | grep -o '"type":"[^"]*"' | cut -d'"' -f4)
        if [ "$chunk_type" = "token" ]; then
            token_data=$(echo "$json_data" | grep -o '"data":"[^"]*"' | cut -d'"' -f4)
            echo -n "$token_data"
        elif [ "$chunk_type" = "sources" ]; then
            echo ""
            echo "[来源] 收到引用来源"
        elif [ "$chunk_type" = "reasoning" ]; then
            echo ""
            echo "[推理链] 收到推理链内容"
        elif [ "$chunk_type" = "done" ]; then
            echo ""
            echo "[完成] 流式传输完成"
        elif [ "$chunk_type" = "error" ]; then
            echo ""
            echo "[错误] 发生错误"
        fi
    fi
done

echo ""
echo ""
echo "=========================================="
echo "测试完成！"
echo ""
echo "💡 提示："
echo "  - 如果看到 token 事件实时输出，说明流式功能正常"
echo "  - 如果一次性输出完整答案，说明不是真正的流式"
echo "  - 使用 --no-buffer 和 -N 参数确保实时输出"
echo ""




