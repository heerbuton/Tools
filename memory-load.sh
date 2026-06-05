#!/bin/bash
# memory-load.sh - 会话开始时加载全局记忆
# 输出全局记忆内容，作为上下文注入会话

MEMORY_FILE="$HOME/.claude/global-memory/memory.md"

if [ -f "$MEMORY_FILE" ]; then
    echo "=== 全局记忆（跨会话持久化） ==="
    cat "$MEMORY_FILE"
    echo ""
    echo "=== 全局记忆结束 ==="
fi
