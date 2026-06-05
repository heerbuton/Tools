#!/bin/bash
# disk-report - 磁盘空间报告脚本
# 用法: disk-report [--top N]

TOP_N=${1:-20}
[[ "$1" == "--top" ]] && TOP_N=${2:-20}

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

get_color() {
    local pct=$1
    if (( pct >= 90 )); then echo "$RED"
    elif (( pct >= 75 )); then echo "$YELLOW"
    else echo "$GREEN"
    fi
}

echo ""
echo -e "${BOLD}=============================="
echo "  磁盘空间报告"
echo -e "==============================${NC}"
echo ""

# --- 各盘使用率 ---
echo -e "${BOLD}▸ 分区使用率${NC}"
printf "  %-6s  %-8s  %-8s  %-8s  %s\n" "盘" "总容量" "已用" "可用" "使用率"
echo "  ------  --------  --------  --------  ------"

df -h 2>/dev/null | grep -iE '^/dev|^C:|^D:|^E:|^F:' | while read -r line; do
    mount=$(echo "$line" | awk '{print $NF}')
    total=$(echo "$line" | awk '{print $2}')
    used=$(echo "$line" | awk '{print $3}')
    avail=$(echo "$line" | awk '{print $4}')
    pct=$(echo "$line" | awk '{print $5}' | sed 's/[^0-9]//g')
    [ -z "$pct" ] && pct=0
    color=$(get_color "$pct")
    printf "  %-8s  %-8s  %-8s  %-8s  ${color}%3s%%${NC}\n" "$mount" "$total" "$used" "$avail" "$pct"
done

# --- 用户目录列表 (不计算大小，避免 Windows du 超时) ---
echo ""
echo -e "${BOLD}▸ 用户目录列表${NC}"
ls -d "$HOME"/*/ 2>/dev/null | while read -r d; do
    name=$(basename "$d")
    printf "  📁 %s\n" "$name"
done

echo ""
echo -e "${BOLD}==============================${NC}"
