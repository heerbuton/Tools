#!/bin/bash
# ai-engine.sh - DeepSeek V4 Pro AI 调用引擎
# 提供 ai_ask / ai_think 函数供其他脚本调用

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载 API Key
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# 检查 API Key
check_api_key() {
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo "错误: 未设置 DEEPSEEK_API_KEY"
        echo "请在 $SCRIPT_DIR/.env 中添加:"
        echo "  DEEPSEEK_API_KEY=your_api_key_here"
        return 1
    fi
}

# 调用 DeepSeek API（普通模式）
# 用法: ai_ask "你的问题"
# 返回: AI 的回答文本
ai_ask() {
    local prompt="$1"
    local system_prompt="${2:-你是一个专业的系统诊断助手，用简洁的中文回答问题。给出具体、可执行的建议。}"

    check_api_key || return 1

    # 用 python 构造 JSON 并调用 API（避免 bash 转义问题）
    python - "$DEEPSEEK_API_KEY" "$system_prompt" "$prompt" << 'PYEOF'
import sys, json, urllib.request

api_key = sys.argv[1]
system_msg = sys.argv[2]
user_msg = sys.argv[3]

data = json.dumps({
    "model": "deepseek-v4-pro",
    "messages": [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ],
    "stream": False
}, ensure_ascii=False).encode("utf-8")

req = urllib.request.Request(
    "https://api.deepseek.com/v1/chat/completions",
    data=data,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)

try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode("utf-8"))
        print(r["choices"][0]["message"]["content"])
except Exception as e:
    print(f"请求失败: {e}")
PYEOF
}

# 带思考模式的调用（显示思考过程 + 最终回答）
# 用法: ai_think "你的问题"
ai_think() {
    local prompt="$1"
    local system_prompt="${2:-你是一个专业的系统诊断助手。先分析问题，再给出具体建议。}"

    check_api_key || return 1

    python - "$DEEPSEEK_API_KEY" "$system_prompt" "$prompt" << 'PYEOF'
import sys, json, urllib.request

api_key = sys.argv[1]
system_msg = sys.argv[2]
user_msg = sys.argv[3]

data = json.dumps({
    "model": "deepseek-v4-pro",
    "messages": [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ],
    "stream": False
}, ensure_ascii=False).encode("utf-8")

req = urllib.request.Request(
    "https://api.deepseek.com/v1/chat/completions",
    data=data,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        r = json.loads(resp.read().decode("utf-8"))
        msg = r["choices"][0]["message"]
        reasoning = msg.get("reasoning_content", "")
        content = msg.get("content", "")
        if reasoning:
            print("=== 思考过程 ===")
            print(reasoning)
            print("")
        print("=== 分析结果 ===")
        print(content)
except Exception as e:
    print(f"请求失败: {e}")
PYEOF
}
