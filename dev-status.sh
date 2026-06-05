#!/bin/bash
# dev-status - 开发环境状态检查
# 用法: dev-status

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

check_tool() {
    local name="$1"
    local cmd="$2"
    local ver_cmd="${3:-$cmd --version}"
    if command -v "$cmd" &>/dev/null; then
        ver=$(eval "$ver_cmd" 2>/dev/null | head -1)
        printf "  ${GREEN}✓${NC} %-18s %s\n" "$name" "$ver"
    else
        printf "  ${RED}✗${NC} %-18s ${DIM}未安装${NC}\n" "$name"
    fi
}

check_service() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        printf "  ${GREEN}●${NC} %-18s ${GREEN}运行中${NC}\n" "$name"
    else
        printf "  ${DIM}○${NC} %-18s ${DIM}未运行${NC}\n" "$name"
    fi
}

echo ""
echo -e "${BOLD}=============================="
echo "  开发环境状态"
echo -e "==============================${NC}"
echo ""

# --- 开发工具 ---
echo -e "${BOLD}▸ 开发工具${NC}"
check_tool "Git" "git" "git --version"
check_tool "Node.js" "node" "node --version"
check_tool "npm" "npm" "npm --version"
check_tool "Python" "python" "python --version"
check_tool "pip" "pip" "pip --version"
check_tool "Conda" "conda" "conda --version"
check_tool "Java" "java" "java -version 2>&1"
check_tool "Docker" "docker" "docker --version"
check_tool "Bun" "bun" "bun --version"
check_tool "Vim" "vim" "vim --version | head -1"
check_tool "VS Code" "code" "code --version | head -1"
check_tool "Ollama" "ollama" "ollama --version"

# --- 服务状态 ---
echo ""
echo -e "${BOLD}▸ 服务状态${NC}"
check_service "Docker Engine" "docker info &>/dev/null"
check_service "Ollama Server" "curl -s http://localhost:11434/api/tags &>/dev/null"

# --- 包管理器 ---
echo ""
echo -e "${BOLD}▸ 包管理器${NC}"
check_tool "npm" "npm" "npm --version"
check_tool "pip" "pip" "pip --version"
check_tool "conda" "conda" "conda --version"
check_tool "choco" "choco" "choco --version"
check_tool "winget" "winget" "winget --version"
check_tool "bun" "bun" "bun --version"

# --- Shell 环境 ---
echo ""
echo -e "${BOLD}▸ Shell 环境${NC}"
printf "  %-18s %s\n" "Shell" "$SHELL"
printf "  %-18s %s\n" "用户" "$(whoami)"
printf "  %-18s %s\n" "主机" "$(hostname)"
printf "  %-18s %s\n" "工作目录" "$(pwd)"
[ -f "$HOME/.bashrc" ] && printf "  ${GREEN}✓${NC} %-18s\n" ".bashrc" || printf "  ${YELLOW}!${NC} %-18s ${YELLOW}缺失${NC}\n" ".bashrc"

echo ""
echo -e "${BOLD}==============================${NC}"
