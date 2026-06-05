#!/bin/bash
# memory - 全局记忆管理工具（小白友好版）
# 用法: memory [命令]
#   memory         - 查看当前记忆
#   memory add     - 添加一条记忆
#   memory edit    - 用记事本编辑记忆文件
#   memory clear   - 清空所有记忆（会确认）

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

MEMORY_FILE="$HOME/.claude/global-memory/memory.md"

# 确保记忆文件存在
if [ ! -f "$MEMORY_FILE" ]; then
    mkdir -p "$(dirname "$MEMORY_FILE")"
    echo "# 全局记忆" > "$MEMORY_FILE"
    echo "" >> "$MEMORY_FILE"
    echo "（还没有任何记忆，用 memory add 添加）" >> "$MEMORY_FILE"
fi

case "${1:-view}" in
    view|"")
        echo ""
        echo -e "${CYAN}${BOLD}====== 全局记忆 ======${NC}"
        echo ""
        cat "$MEMORY_FILE"
        echo ""
        echo -e "${CYAN}=======================${NC}"
        echo -e "  记忆文件: $MEMORY_FILE"
        echo -e "  提示: 输入 ${GREEN}memory add${NC} 添加新记忆"
        echo ""
        ;;

    add)
        echo ""
        echo -e "${YELLOW}请输入要记住的内容（输入完按回车）:${NC}"
        echo ""
        read -r content
        if [ -n "$content" ]; then
            echo "" >> "$MEMORY_FILE"
            echo "- [$content]" >> "$MEMORY_FILE"
            echo ""
            echo -e "${GREEN}✓ 已记住: $content${NC}"
        else
            echo -e "${RED}内容为空，未保存${NC}"
        fi
        echo ""
        ;;

    edit)
        echo ""
        echo -e "${YELLOW}正在打开记忆文件...${NC}"
        if command -v code &>/dev/null; then
            code "$MEMORY_FILE"
        elif command -v notepad &>/dev/null; then
            notepad "$MEMORY_FILE"
        else
            vim "$MEMORY_FILE"
        fi
        ;;

    clear)
        echo ""
        echo -e "${RED}${BOLD}⚠ 警告: 这将清空所有全局记忆！${NC}"
        echo -e "  当前记忆内容:"
        cat "$MEMORY_FILE" | head -10
        echo ""
        read -p "  确认清空？(输入 yes 确认): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "# 全局记忆" > "$MEMORY_FILE"
            echo -e "${GREEN}✓ 记忆已清空${NC}"
        else
            echo -e "${YELLOW}已取消${NC}"
        fi
        echo ""
        ;;

    help|--help|-h)
        echo ""
        echo -e "${BOLD}memory - 全局记忆管理工具${NC}"
        echo ""
        echo "  memory         查看当前记忆"
        echo "  memory add     添加一条记忆"
        echo "  memory edit    用编辑器打开记忆文件"
        echo "  memory clear   清空所有记忆"
        echo "  memory help    显示帮助"
        echo ""
        ;;

    *)
        echo -e "${RED}未知命令: $1${NC}"
        echo "输入 memory help 查看帮助"
        ;;
esac
