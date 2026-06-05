#!/bin/bash
# memory-save.sh - 接收会话摘要并追加到全局记忆
# 用法: echo "摘要内容" | bash memory-save.sh

MEMORY_FILE="$HOME/.claude/global-memory/memory.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# 从 stdin 读取输入
INPUT=$(cat)

if [ -z "$INPUT" ]; then
    echo '{"status":"empty","message":"No input provided"}'
    exit 0
fi

# 追加到记忆文件
echo "" >> "$MEMORY_FILE"
echo "### [$TIMESTAMP] 会话记录" >> "$MEMORY_FILE"
echo "$INPUT" >> "$MEMORY_FILE"

echo '{"status":"ok","message":"Memory saved"}'
