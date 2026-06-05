#!/bin/bash
# ai-clean.sh - AI 智能诊断 + 清理
# 扫描 → DeepSeek 分析分级 → 用户确认 → 执行清理

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

source "$SCRIPT_DIR/ai-engine.sh"
check_api_key || exit 1

echo ""
echo -e "${CYAN}${BOLD}================================${NC}"
echo -e "${CYAN}${BOLD}    AI 智能诊断与清理${NC}"
echo -e "${CYAN}${BOLD}================================${NC}"
echo ""

# ===== Step 1: 扫描（只读） =====
echo -e "${YELLOW}[1/5] 扫描磁盘...${NC}"
DISK_INFO=$(df -h 2>/dev/null | grep -iE '^C:|^D:|^E:|^F:')

echo -e "${YELLOW}[2/5] 扫描开发环境...${NC}"
DEV_INFO=""
for cmd_info in "Git:git:git --version" "Node.js:node:node --version" "Python:python:python --version" "Java:java:java -version 2>&1" "Docker:docker:docker --version" "Conda:conda:conda --version"; do
    IFS=: read name cmd ver_cmd <<< "$cmd_info"
    if command -v "$cmd" &>/dev/null; then
        ver=$($ver_cmd 2>/dev/null | head -1)
        DEV_INFO+="$name: $ver\n"
    else
        DEV_INFO+="$name: 未安装\n"
    fi
done

echo -e "${YELLOW}[3/5] 扫描可清理项目...${NC}"
CLEAN_SCAN=""
# 用户目录日志
for f in "$HOME"/java_error_in_pycharm64_*.log "$HOME/jmeter.log" "$HOME/mumu_boot.txt"; do
    [ -f "$f" ] && CLEAN_SCAN+="LOG | $(basename "$f") | $(du -sh "$f" 2>/dev/null | cut -f1) | $f\n"
done
# 过时安装脚本
[ -f "$HOME/msfinstall" ] && CLEAN_SCAN+="LOG | msfinstall | $(du -sh "$HOME/msfinstall" 2>/dev/null | cut -f1) | $HOME/msfinstall\n"
# Claude 缓存
for dir in "$HOME/.claude/telemetry" "$HOME/.claude/paste-cache" "$HOME/.claude/shell-snapshots"; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        count=$(ls "$dir" 2>/dev/null | wc -l)
        [ "$count" -gt 0 ] && CLEAN_SCAN+="CACHE | $(basename "$dir") ($count 个文件) | $size | $dir\n"
    fi
done
# Temp 目录（7天前）
TEMP_DIR="$HOME/AppData/Local/Temp"
if [ -d "$TEMP_DIR" ]; then
    count=$(find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        size=$(find "$TEMP_DIR" -maxdepth 1 -mtime +7 -type f -exec du -ch {} + 2>/dev/null | tail -1 | cut -f1)
        CLEAN_SCAN+="CACHE | Temp 7天前文件 ($count 个) | $size | $TEMP_DIR\n"
    fi
fi
# npm/pip/conda 缓存
[ -d "$HOME/.npm" ] && CLEAN_SCAN+="CACHE | npm 缓存 | $(du -sh "$HOME/.npm" 2>/dev/null | cut -f1) | $HOME/.npm\n"
[ -d "$HOME/.cache/pip" ] && CLEAN_SCAN+="CACHE | pip 缓存 | $(du -sh "$HOME/.cache/pip" 2>/dev/null | cut -f1) | $HOME/.cache/pip\n"
# 根目录 node_modules
[ -d "$HOME/node_modules" ] && CLEAN_SCAN+="CACHE | 根目录 node_modules | $(du -sh "$HOME/node_modules" 2>/dev/null | cut -f1) | $HOME/node_modules\n"

echo -e "${YELLOW}[4/5] 请求 DeepSeek V4 Pro 分析...${NC}"

# ===== Step 2: AI 分析分级（用 python 调用避免 shell 转义问题） =====
JSON_DATA=$(python - "$SCRIPT_DIR" "$DISK_INFO" "$DEV_INFO" "$CLEAN_SCAN" << 'PYEOF'
import sys, os, json

# 加载 ai-engine
script_dir = sys.argv[1]
sys.path.insert(0, script_dir)

# 直接用 urllib 调用 DeepSeek
import urllib.request

api_key = None
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.startswith('DEEPSEEK_API_KEY='):
                api_key = line.strip().split('=', 1)[1]
                break

if not api_key:
    print('{}')
    sys.exit(1)

disk_info = sys.argv[2]
dev_info = sys.argv[3].replace('\\n', '\n')
clean_scan = sys.argv[4].replace('\\n', '\n')

prompt = f"""请分析以下 Windows 11 系统数据，按三级分类给出清理建议。

## 磁盘
{disk_info}

## 开发环境
{dev_info}

## 扫描到的可清理项（格式：类型 | 名称 | 大小 | 路径）
{clean_scan}

请严格按以下 JSON 格式输出（不要输出其他内容）：
{chr(96)}{chr(96)}{chr(96)}json
{{
  "summary": "一句话总览",
  "green": [
    {{"name": "名称", "size": "大小", "path": "路径", "cmd": "清理命令", "note": "说明"}}
  ],
  "yellow": [
    {{"name": "名称", "size": "大小", "path": "路径", "reason": "需要判断的原因", "options": ["选项1", "选项2"]}}
  ],
  "red": [
    {{"name": "名称", "size": "大小", "reason": "不建议清理的原因"}}
  ],
  "advice": "其他优化建议"
}}
{chr(96)}{chr(96)}{chr(96)}

规则：
- green（可自动清理）：纯缓存、临时文件、日志、明确可再生且不影响功能
- yellow（需人工判断）：可能有用但占空间，需要用户决定
- red（谨慎清理）：不建议动的
- 每个 green 项必须给出可执行的清理命令（用 rm -rf 或 find -delete）
- 大小用"约 XX MB/GB"格式
- 用中文回答"""

data = json.dumps({
    "model": "deepseek-v4-pro",
    "messages": [
        {"role": "system", "content": "你是存储分析专家。只输出JSON，不要多余文字。"},
        {"role": "user", "content": prompt}
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
        content = r["choices"][0]["message"]["content"]
        # 提取 JSON 块
        import re
        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            print(match.group(1))
        else:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                print(match.group(0))
            else:
                print(content)
except Exception as e:
    print(json.dumps({"summary": f"请求失败: {e}", "green": [], "yellow": [], "red": [], "advice": ""}))
PYEOF
)

# ===== Step 3: 展示结果 =====
echo ""
echo -e "${CYAN}${BOLD}========== 诊断结果 ==========${NC}"
echo ""

python - "$JSON_DATA" << 'PYEOF'
import sys, json

try:
    data = json.loads(sys.argv[1])
except:
    print("解析失败，原始结果：")
    print(sys.argv[1])
    sys.exit(0)

GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'

print(f"{CYAN}总览：{data.get('summary', '无')}{NC}")
print()

greens = data.get('green', [])
if greens:
    print(f"{GREEN}{BOLD}🟢 可自动清理（安全删除）：{NC}")
    for i, item in enumerate(greens, 1):
        print(f"  {GREEN}[{i}]{NC} {item['name']}  {item['size']}")
        print(f"      路径: {item['path']}")
        print(f"      命令: {item['cmd']}")
        if item.get('note'):
            print(f"      说明: {item['note']}")
    print()

yellows = data.get('yellow', [])
if yellows:
    print(f"{YELLOW}{BOLD}🟡 需要你判断：{NC}")
    for i, item in enumerate(yellows, 1):
        print(f"  {YELLOW}[{i}]{NC} {item['name']}  {item['size']}")
        print(f"      路径: {item['path']}")
        print(f"      原因: {item['reason']}")
        if item.get('options'):
            for j, opt in enumerate(item['options'], 1):
                print(f"      选项{j}: {opt}")
    print()

reds = data.get('red', [])
if reds:
    print(f"{RED}{BOLD}🔴 不建议清理：{NC}")
    for i, item in enumerate(reds, 1):
        print(f"  {RED}[{i}]{NC} {item['name']}  {item.get('size', '')}")
        print(f"      原因: {item['reason']}")
    print()

advice = data.get('advice', '')
if advice:
    print(f"{CYAN}其他建议：{advice}{NC}")
    print()
PYEOF

# ===== Step 4: 用户确认清理 =====
echo -e "${CYAN}--------------------------------${NC}"
echo ""
echo -e "${BOLD}选择操作：${NC}"
echo -e "  ${GREEN}a${NC}) 清理所有 🟢 项目"
echo -e "  ${GREEN}数字${NC}) 清理指定 🟢 项目（如 1,3 表示第1和第3项）"
echo -e "  ${YELLOW}s${NC}) 仅查看，不清理"
echo ""
read -p "  你的选择: " choice

if [ "$choice" = "s" ] || [ -z "$choice" ]; then
    echo -e "\n${YELLOW}已跳过清理。${NC}"
    exit 0
fi

# 执行清理
if [ "$choice" = "a" ]; then
    echo ""
    echo -e "${RED}即将清理所有 🟢 项目，确认吗？(y/N)${NC}"
    read -p "  " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "\n${YELLOW}已取消。${NC}"
        exit 0
    fi
    echo ""
    echo -e "${CYAN}开始清理...${NC}"
    python - "$JSON_DATA" "all" << 'PYEOF'
import sys, json, subprocess, os

data = json.loads(sys.argv[1])
greens = data.get('green', [])
home = os.path.expanduser("~")

for i, item in enumerate(greens, 1):
    name = item['name']
    path = item['path']
    cmd = item['cmd']
    print(f"\n  [{i}/{len(greens)}] 清理: {name}")
    if not path.startswith(home) and not path.startswith('/c/Users'):
        print(f"    ⚠ 跳过：路径不在用户目录内")
        continue
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"    ✓ 完成")
        else:
            print(f"    ✗ 失败: {result.stderr[:100]}")
    except Exception as e:
        print(f"    ✗ 错误: {e}")

print("\n清理完成！")
PYEOF
else
    echo ""
    echo -e "${RED}即将清理选中的 🟢 项目，确认吗？(y/N)${NC}"
    read -p "  " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo -e "\n${YELLOW}已取消。${NC}"
        exit 0
    fi
    echo ""
    echo -e "${CYAN}开始清理...${NC}"
    python - "$JSON_DATA" "$choice" << 'PYEOF'
import sys, json, subprocess, os

data = json.loads(sys.argv[1])
selected = [int(x.strip()) for x in sys.argv[2].split(',')]
greens = data.get('green', [])
home = os.path.expanduser("~")

for idx in selected:
    if idx < 1 or idx > len(greens):
        print(f"  ⚠ 项目 [{idx}] 不存在，跳过")
        continue
    item = greens[idx - 1]
    name = item['name']
    path = item['path']
    cmd = item['cmd']
    print(f"\n  清理 [{idx}]: {name}")
    if not path.startswith(home) and not path.startswith('/c/Users'):
        print(f"    ⚠ 跳过：路径不在用户目录内")
        continue
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"    ✓ 完成")
        else:
            print(f"    ✗ 失败: {result.stderr[:100]}")
    except Exception as e:
        print(f"    ✗ 错误: {e}")

print("\n清理完成！")
PYEOF
fi

echo ""
echo -e "${CYAN}================================${NC}"
echo -e "清理完成。运行 ${GREEN}tools${NC} → 3 查看当前磁盘空间。"
echo ""
