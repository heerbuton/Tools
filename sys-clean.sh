#!/bin/bash
# sys-clean - 一键系统清理脚本
# 用法: sys-clean [--dry-run]

DRY_RUN=false
[[ "$1" == "--dry-run" ]] && DRY_RUN=true

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cleaned=0

log_ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
log_skip() { echo -e "  ${YELLOW}[跳过]${NC} $1"; }
log_dry()  { echo -e "  ${YELLOW}[预览]${NC} $1"; }

do_rm() {
    local target="$1"
    local desc="$2"
    if [ ! -e "$target" ]; then
        log_skip "$desc (不存在)"
        return
    fi
    local size
    size=$(du -sh "$target" 2>/dev/null | cut -f1)
    if $DRY_RUN; then
        log_dry "$desc ($size): $target"
    else
        rm -rf "$target"
        log_ok "$desc ($size)"
    fi
    ((cleaned++))
}

echo ""
echo "=============================="
echo "  sys-clean 系统清理工具"
echo "=============================="
$DRY_RUN && echo -e "  ${YELLOW}** 预览模式，不会实际删除 **${NC}"
echo ""

# --- Claude Code 缓存 ---
echo "▸ Claude Code 缓存"
do_rm "$HOME/.claude/telemetry/1p_failed_events."*".json" "失败的遥测事件"
do_rm "$HOME/.claude/paste-cache" "粘贴缓存"
do_rm "$HOME/.claude/shell-snapshots" "Shell 快照"

# --- 用户目录垃圾 ---
echo ""
echo "▸ 用户目录垃圾文件"
for f in "$HOME"/java_error_in_pycharm64_*.log; do
    [ -f "$f" ] && do_rm "$f" "PyCharm 错误日志"
done
[ -f "$HOME/jmeter.log" ] && do_rm "$HOME/jmeter.log" "JMeter 日志"
[ -f "$HOME/mumu_boot.txt" ] && do_rm "$HOME/mumu_boot.txt" "Mumu 启动日志"
[ -f "$HOME/msfinstall" ] && do_rm "$HOME/msfinstall" "Metasploit 安装脚本"

# --- Temp 目录 (7天前) ---
echo ""
echo "▸ Temp 目录 (7天前文件)"
TEMP_DIR="$HOME/AppData/Local/Temp"
if [ -d "$TEMP_DIR" ]; then
    if $DRY_RUN; then
        count=$(find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f 2>/dev/null | wc -l)
        size=$(find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
        log_dry "Temp 7天前文件: ${count}个, ${size:-0}"
    else
        find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f -delete 2>/dev/null
        log_ok "Temp 7天前文件已清理"
    fi
    ((cleaned++))
fi

# --- 报告 ---
echo ""
echo "=============================="
if $DRY_RUN; then
    echo -e "  预览完成，发现 ${cleaned} 项可清理"
    echo -e "  运行 ${GREEN}sys-clean${NC} (不带 --dry-run) 执行实际清理"
else
    echo -e "  ${GREEN}清理完成${NC}，处理了 ${cleaned} 项"
fi
echo "=============================="
echo ""
df -h /c /d /e /f 2>/dev/null | head -5
