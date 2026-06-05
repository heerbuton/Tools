#!/bin/bash
# ai-diagnose.sh - AI 智能系统诊断
# 收集系统数据 → 发送给 DeepSeek V4 Pro → 输出分析建议

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# 加载 AI 引擎
source "$SCRIPT_DIR/ai-engine.sh"

echo ""
echo -e "${CYAN}${BOLD}================================${NC}"
echo -e "${CYAN}${BOLD}    AI 智能系统诊断${NC}"
echo -e "${CYAN}${BOLD}================================${NC}"
echo ""

# 检查 API Key
check_api_key || exit 1

# ===== 收集数据 =====
echo -e "${YELLOW}[1/4] 收集磁盘信息...${NC}"
DISK_INFO=$(df -h 2>/dev/null | grep -iE '^/dev|^C:|^D:|^E:|^F:')

echo -e "${YELLOW}[2/4] 收集开发环境状态...${NC}"
DEV_INFO=""
check() {
    if command -v "$2" &>/dev/null; then
        ver=$($3 2>/dev/null | head -1)
        DEV_INFO+="  $1: $ver\n"
    else
        DEV_INFO+="  $1: 未安装\n"
    fi
}
check "Git" git "git --version"
check "Node.js" node "node --version"
check "Python" python "python --version"
check "Java" java "java -version 2>&1"
check "Docker" docker "docker --version"
check "Conda" conda "conda --version"
check "VS Code" code "code --version 2>/dev/null | head -1"

echo -e "${YELLOW}[3/4] 收集可清理项目...${NC}"
CLEAN_ITEMS=""
[ -f "$HOME/jmeter.log" ] && CLEAN_ITEMS+="  - jmeter.log ($(du -sh "$HOME/jmeter.log" 2>/dev/null | cut -f1))\n"
for f in "$HOME"/java_error_in_pycharm64_*.log; do
    [ -f "$f" ] && CLEAN_ITEMS+="  - $(basename $f) ($(du -sh "$f" 2>/dev/null | cut -f1))\n"
done
[ -d "$HOME/.claude/telemetry" ] && {
    count=$(ls "$HOME/.claude/telemetry"/1p_failed_events.*.json 2>/dev/null | wc -l)
    [ "$count" -gt 0 ] && CLEAN_ITEMS+="  - Claude telemetry: $count 个失败事件\n"
}

echo -e "${YELLOW}[4/4] 构造诊断请求...${NC}"

# ===== 构造 Prompt =====
PROMPT="请分析以下 Windows 11 系统状况，给出优化建议：

## 磁盘使用情况
$DISK_INFO

## 开发环境
$(echo -e "$DEV_INFO")

## 可清理项目
$(echo -e "$CLEAN_ITEMS")

请从以下角度分析：
1. 磁盘空间是否紧张？哪个盘需要重点关注？
2. 开发环境配置是否合理？有无缺失或冲突？
3. 哪些清理项目是安全的？有无需要注意的？
4. 有没有其他优化建议？

请用简洁的中文回答，给出具体可执行的操作步骤。"

echo ""
echo -e "${CYAN}正在请求 DeepSeek V4 Pro 分析...${NC}"
echo ""

# ===== 调用 AI =====
ai_think "$PROMPT"

echo ""
echo -e "${CYAN}================================${NC}"
echo -e "诊断完成。建议在 Claude Code 中执行具体操作。"
echo ""
