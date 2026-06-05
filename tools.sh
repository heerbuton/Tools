#!/bin/bash
# tools - 电脑维护工具箱（小白友好版）
# 使用方法: 在终端输入 bash ~/scripts/tools.sh 或 tools

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

show_menu() {
    clear
    echo ""
    echo -e "${CYAN}${BOLD}================================${NC}"
    echo -e "${CYAN}${BOLD}    电脑维护工具箱 v1.0${NC}"
    echo -e "${CYAN}${BOLD}================================${NC}"
    echo ""
    echo -e "  ${GREEN}1${NC}) 查看电脑状态        (开发工具/服务/磁盘)"
    echo -e "  ${GREEN}2${NC}) 清理垃圾文件        (缓存/日志/临时文件)"
    echo -e "  ${GREEN}3${NC}) 查看磁盘空间        (各盘使用率)"
    echo -e "  ${GREEN}4${NC}) 清理 Claude 缓存    (telemetry/快照)"
    echo -e "  ${GREEN}5${NC}) AI 智能诊断        (DeepSeek 分析系统状况)"
    echo ""
    echo -e "  ${YELLOW}0${NC}) 退出"
    echo ""
    echo -e "${CYAN}--------------------------------${NC}"
}

pause() {
    echo ""
    read -p "按回车键返回菜单..." _
}

# ============ 功能1: 查看电脑状态 ============
func_status() {
    clear
    echo ""
    echo -e "${BOLD}========== 电脑状态检查 ==========${NC}"
    echo ""

    echo -e "${BOLD}[1/3] 开发工具${NC}"
    check() {
        if command -v "$2" &>/dev/null; then
            ver=$($3 2>/dev/null | head -1)
            echo -e "  ${GREEN}✓${NC} $1  →  $ver"
        else
            echo -e "  ${RED}✗${NC} $1  →  未安装"
        fi
    }
    check "Git"      git     "git --version"
    check "Node.js"  node    "node --version"
    check "Python"   python  "python --version"
    check "Java"     java    "java -version 2>&1"
    check "Docker"   docker  "docker --version"
    check "Conda"    conda   "conda --version"
    check "VS Code"  code    "code --version 2>/dev/null | head -1"

    echo ""
    echo -e "${BOLD}[2/3] 服务状态${NC}"
    if docker info &>/dev/null 2>&1; then
        echo -e "  ${GREEN}●${NC} Docker Engine  →  运行中"
    else
        echo -e "  ${YELLOW}○${NC} Docker Engine  →  未运行"
    fi
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        echo -e "  ${GREEN}●${NC} Ollama Server  →  运行中"
    else
        echo -e "  ${YELLOW}○${NC} Ollama Server  →  未运行"
    fi

    echo ""
    echo -e "${BOLD}[3/3] 磁盘使用率${NC}"
    printf "  %-8s  %-8s  %-8s  %-8s  %s\n" "盘" "总容量" "已用" "可用" "使用率"
    df -h 2>/dev/null | grep -iE '^/dev|^C:|^D:|^E:|^F:' | while read -r line; do
        mount=$(echo "$line" | awk '{print $NF}')
        total=$(echo "$line" | awk '{print $2}')
        used=$(echo "$line" | awk '{print $3}')
        avail=$(echo "$line" | awk '{print $4}')
        pct=$(echo "$line" | awk '{print $5}' | sed 's/[^0-9]//g')
        [ -z "$pct" ] && pct=0
        if (( pct >= 90 )); then c="$RED"
        elif (( pct >= 75 )); then c="$YELLOW"
        else c="$GREEN"
        fi
        printf "  %-8s  %-8s  %-8s  %-8s  ${c}%3s%%${NC}\n" "$mount" "$total" "$used" "$avail" "$pct"
    done

    pause
}

# ============ 功能2: 清理垃圾文件 ============
func_clean() {
    clear
    echo ""
    echo -e "${BOLD}========== 清理垃圾文件 ==========${NC}"
    echo ""

    total_freed=0

    clean_item() {
        local target="$1" desc="$2"
        if [ ! -e "$target" ]; then
            return
        fi
        local size
        size=$(du -sh "$target" 2>/dev/null | cut -f1)
        echo -e "  清理: $desc ($size)"
        rm -rf "$target"
    }

    echo -e "${YELLOW}[1/4] 清理日志文件...${NC}"
    for f in "$HOME"/java_error_in_pycharm64_*.log; do
        [ -f "$f" ] && clean_item "$f" "PyCharm错误日志"
    done
    [ -f "$HOME/jmeter.log" ] && clean_item "$HOME/jmeter.log" "JMeter日志"
    [ -f "$HOME/mumu_boot.txt" ] && clean_item "$HOME/mumu_boot.txt" "Mumu日志"

    echo -e "${YELLOW}[2/4] 清理旧临时文件(7天前)...${NC}"
    TEMP_DIR="$HOME/AppData/Local/Temp"
    if [ -d "$TEMP_DIR" ]; then
        count=$(find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f -delete 2>/dev/null
            echo -e "  已清理 $count 个临时文件"
        else
            echo -e "  没有需要清理的临时文件"
        fi
    fi

    echo -e "${YELLOW}[3/4] 清理过时安装脚本...${NC}"
    [ -f "$HOME/msfinstall" ] && clean_item "$HOME/msfinstall" "Metasploit安装脚本"

    echo -e "${YELLOW}[4/4] 清理Claude粘贴缓存...${NC}"
    [ -d "$HOME/.claude/paste-cache" ] && clean_item "$HOME/.claude/paste-cache" "Claude粘贴缓存"

    echo ""
    echo -e "${GREEN}清理完成！${NC}"
    pause
}

# ============ 功能3: 查看磁盘空间 ============
func_disk() {
    clear
    echo ""
    echo -e "${BOLD}========== 磁盘空间 ==========${NC}"
    echo ""
    printf "  %-8s  %-8s  %-8s  %-8s  %s\n" "盘" "总容量" "已用" "可用" "使用率"
    echo "  ------  --------  --------  --------  ------"
    df -h 2>/dev/null | grep -iE '^/dev|^C:|^D:|^E:|^F:' | while read -r line; do
        mount=$(echo "$line" | awk '{print $NF}')
        total=$(echo "$line" | awk '{print $2}')
        used=$(echo "$line" | awk '{print $3}')
        avail=$(echo "$line" | awk '{print $4}')
        pct=$(echo "$line" | awk '{print $5}' | sed 's/[^0-9]//g')
        [ -z "$pct" ] && pct=0
        if (( pct >= 90 )); then c="$RED"
        elif (( pct >= 75 )); then c="$YELLOW"
        else c="$GREEN"
        fi
        printf "  %-8s  %-8s  %-8s  %-8s  ${c}%3s%%${NC}\n" "$mount" "$total" "$used" "$avail" "$pct"
    done
    echo ""
    echo -e "  ${RED}红色${NC}=快满了(>90%)  ${YELLOW}黄色${NC}=注意(>75%)  ${GREEN}绿色${NC}=正常"
    pause
}

# ============ 功能4: 清理Claude缓存 ============
func_claude() {
    clear
    echo ""
    echo -e "${BOLD}========== 清理 Claude 缓存 ==========${NC}"
    echo ""

    echo -e "${YELLOW}[1/3] 清理失败的遥测事件...${NC}"
    telem_dir="$HOME/.claude/telemetry"
    if [ -d "$telem_dir" ]; then
        count=$(ls "$telem_dir"/1p_failed_events.*.json 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            rm -f "$telem_dir"/1p_failed_events.*.json
            echo -e "  已清理 $count 个失败事件文件"
        else
            echo -e "  没有需要清理的文件"
        fi
    fi

    echo -e "${YELLOW}[2/3] 清理Shell快照...${NC}"
    snap_dir="$HOME/.claude/shell-snapshots"
    if [ -d "$snap_dir" ]; then
        count=$(ls "$snap_dir" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            rm -rf "$snap_dir"/*
            echo -e "  已清理 $count 个Shell快照"
        else
            echo -e "  没有需要清理的快照"
        fi
    fi

    echo -e "${YELLOW}[3/3] 清理粘贴缓存...${NC}"
    paste_dir="$HOME/.claude/paste-cache"
    if [ -d "$paste_dir" ]; then
        count=$(ls "$paste_dir" 2>/dev/null | wc -l)
        if [ "$count" -gt 0 ]; then
            rm -rf "$paste_dir"/*
            echo -e "  已清理 $count 个粘贴缓存"
        else
            echo -e "  没有需要清理的缓存"
        fi
    fi

    echo ""
    echo -e "${GREEN}Claude 缓存清理完成！${NC}"
    pause
}

# ============ 主循环 ============
while true; do
    show_menu
    read -p "  请选择功能 [0-5]: " choice
    case $choice in
        1) func_status ;;
        2) func_clean ;;
        3) func_disk ;;
        4) func_claude ;;
        5) bash /f/Toolbox/ai-diagnose.sh; pause ;;
        0) echo -e "\n  ${GREEN}再见！${NC}\n"; exit 0 ;;
        *) echo -e "\n  ${RED}无效选项，请输入 0-5${NC}"; sleep 1 ;;
    esac
done
