# Toolbox - 电脑维护工具箱

一套轻量级的 Windows 电脑维护工具，集成 DeepSeek V4 Pro AI 智能诊断与清理。提供两种使用方式：

- **GUI 可视化版** — 双击 `Toolbox.exe` 即可使用，无需命令行
- **CLI 命令行版** — 在 Git Bash 中输入 `tools` 使用

## 快速开始

### GUI 可视化版（推荐）

双击 `F:\Toolbox\Toolbox.exe` 打开图形界面，点击按钮即可使用所有功能。

### CLI 命令行版

打开 Git Bash，输入以下任意命令：

```bash
tools       # 打开工具箱主菜单
memory      # 管理全局记忆
```

## 工具清单

### 1. tools - 工具箱主菜单

交互式菜单，输入数字选择功能：

```
================================
    电脑维护工具箱 v1.0
================================

  1) 查看电脑状态        (开发工具/服务/磁盘)
  2) 清理垃圾文件        (缓存/日志/临时文件)
  3) 查看磁盘空间        (各盘使用率)
  4) 清理 Claude 缓存    (telemetry/快照)
  5) AI 智能诊断        (DeepSeek 分析系统状况)
  6) AI 智能清理        (诊断+分类+一键清理)

  0) 退出
```

**功能说明：**

| 功能 | 说明 | 安全性 |
|------|------|--------|
| 查看电脑状态 | 检测 Git/Node/Python/Java/Docker/Conda/VS Code 版本，显示服务状态和磁盘使用率 | 只读，完全安全 |
| 清理垃圾文件 | 清理 PyCharm 错误日志、JMeter 日志、7天前的临时文件、过时安装脚本 | 仅删除明确无用的文件 |
| 查看磁盘空间 | 显示 C/D/E/F 盘使用率，红黄绿三色标注 | 只读，完全安全 |
| 清理 Claude 缓存 | 清理失败的遥测事件、Shell 快照、粘贴缓存 | 仅删除 Claude 产生的临时文件 |
| AI 智能诊断 | 收集系统数据，发送给 DeepSeek V4 Pro 分析，输出优化建议 | 只读，数据仅发送给 DeepSeek API |
| AI 智能清理 | 诊断 + 三级分类（🟢自动清/🟡需判断/🔴谨慎）+ 用户确认后执行清理 | 需用户确认，仅清理 🟢 项目 |

### 2. memory - 全局记忆管理

```bash
memory         # 查看当前记忆
memory add     # 添加一条记忆（交互式输入）
memory edit    # 用 VS Code / 记事本打开记忆文件
memory clear   # 清空所有记忆（需输入 yes 确认）
memory help    # 显示帮助
```

**记忆文件位置：** `C:\Users\DELL\.claude\global-memory\memory.md`

**自动加载：** 每次新开 Claude Code 会话时，记忆会自动注入上下文。

**自动保存：** 会话结束时，Claude 会自动检查是否有新信息值得保存到记忆文件。

### 3. 独立脚本（可直接调用）

| 脚本 | 命令 | 说明 |
|------|------|------|
| `ai-engine.sh` | `source /f/Toolbox/ai-engine.sh` | AI 调用引擎，提供 `ai_ask` 和 `ai_think` 函数 |
| `ai-diagnose.sh` | `bash /f/Toolbox/ai-diagnose.sh` | AI 智能系统诊断（只读分析） |
| `ai-clean.sh` | `bash /f/Toolbox/ai-clean.sh` | AI 智能诊断+清理（三级分类+确认执行） |
| `sys-clean.sh` | `bash /f/Toolbox/sys-clean.sh [--dry-run]` | 系统清理，支持预览模式 |
| `disk-report.sh` | `bash /f/Toolbox/disk-report.sh` | 磁盘空间报告 |
| `dev-status.sh` | `bash /f/Toolbox/dev-status.sh` | 开发环境状态检查 |
| `memory-load.sh` | `bash /f/Toolbox/memory-load.sh` | 加载全局记忆（hook 用） |
| `memory-save.sh` | `bash /f/Toolbox/memory-save.sh` | 保存记忆（hook 用） |

## AI 智能诊断

工具箱集成了 DeepSeek V4 Pro 思考模式，可以智能分析系统状况并给出优化建议。

### 使用方式

**方式一：菜单调用**
```bash
tools
# 选择 5) AI 智能诊断
```

**方式二：直接调用**
```bash
bash /f/Toolbox/ai-diagnose.sh
```

**方式三：在脚本中调用 AI 引擎**
```bash
source /f/Toolbox/ai-engine.sh

# 普通问答
ai_ask "如何清理 Docker 缓存？"

# 带思考过程的问答
ai_think "分析我的系统为什么变慢了"
```

### AI 诊断会分析什么

1. **磁盘使用情况** — 哪个盘需要重点关注，是否紧张
2. **开发环境配置** — 是否合理，有无缺失或冲突
3. **可清理项目** — 哪些是安全的，有无需要注意的
4. **优化建议** — 具体可执行的操作步骤

### AI 智能清理

在诊断基础上，增加三级分类和执行清理能力：

| 分类 | 含义 | 操作 |
|------|------|------|
| 🟢 可自动清理 | 纯缓存、临时文件、日志，删了不影响功能 | 确认后自动执行 |
| 🟡 需要你判断 | 可能有用但占空间，需要你决定 | 显示原因和选项，不自动执行 |
| 🔴 不建议清理 | 系统文件、核心数据，动了可能出问题 | 仅展示，不提供操作 |

**使用方式：**
```bash
# 菜单调用
tools → 选 6

# 直接调用
bash /f/Toolbox/ai-clean.sh
```

**执行流程：**
1. 扫描磁盘、开发环境、可清理项目
2. DeepSeek V4 Pro 分析并分级
3. 展示三级分类结果
4. 用户选择：清理全部 🟢 / 清理指定 🟢 / 仅查看
5. 二次确认后执行清理

### API 配置

API Key 存储在 `F:\Toolbox\.env`：

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

如需更换 Key，直接编辑此文件即可。

## 安装与配置

### 前置条件

- Windows 10/11
- Git Bash（安装 Git for Windows 自带）
- Python 3.x（用于 JSON 解析和 API 调用）
- 网络连接（AI 诊断功能需要）

### 安装步骤

1. 确保 `F:\Toolbox` 目录存在
2. 在 `~/.bashrc` 中添加以下内容（如果还没有）：

```bash
# 工具箱
export PATH="/f/Toolbox:$PATH"
alias tools='bash /f/Toolbox/tools.sh'
alias tool='bash /f/Toolbox/tools.sh'
alias toolbox='bash /f/Toolbox/tools.sh'
alias memory='bash /f/Toolbox/memory.sh'
```

3. 重新加载配置：

```bash
source ~/.bashrc
```

4. 验证安装：

```bash
tools    # 应该看到工具箱菜单
memory   # 应该看到全局记忆
```

### Claude Code 全局记忆配置

在 `C:\Users\DELL\.claude\settings.json` 中的 hooks 部分应包含：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "shell": "bash",
            "command": "bash /f/Toolbox/memory-load.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "shell": "bash",
            "command": "bash /f/Toolbox/memory-load.sh",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "shell": "bash",
            "command": "echo '[记忆系统] 请检查是否需要更新 ~/.claude/global-memory/memory.md'",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## 文件结构

```
F:\Toolbox\
├── README.md              # 本文档
├── Toolbox.exe            # GUI 可视化版（双击运行）
├── .env                   # DeepSeek API Key（不提交版本控制）
├── tools.sh               # 工具箱主菜单（CLI 入口）
├── memory.sh              # 全局记忆管理
├── memory-load.sh         # 记忆加载（SessionStart hook）
├── memory-save.sh         # 记忆保存（Stop hook）
├── ai-engine.sh           # DeepSeek V4 Pro AI 调用引擎
├── ai-diagnose.sh         # AI 智能系统诊断（只读）
├── ai-clean.sh            # AI 智能诊断+清理（三级分类）
├── sys-clean.sh           # 系统清理（支持 --dry-run）
├── disk-report.sh         # 磁盘空间报告
├── dev-status.sh          # 开发环境状态检查
└── gui/
    ├── toolbox_gui.py     # GUI 源码
    └── build.bat          # 打包脚本
```

## 常见问题

**Q: 输入 tools 提示命令找不到？**
A: 运行 `source ~/.bashrc` 重新加载配置，或检查 `~/.bashrc` 中是否有工具箱的 PATH 和 alias 配置。

**Q: AI 诊断提示 API Key 错误？**
A: 检查 `F:\Toolbox\.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确。

**Q: AI 诊断超时？**
A: 检查网络连接。DeepSeek API 在国内可直接访问，如遇网络问题可尝试更换网络环境。

**Q: 清理垃圾文件会不会删错东西？**
A: 不会。脚本只清理明确无用的文件（PyCharm 错误日志、7天前临时文件等），不会触碰项目代码或配置文件。

**Q: 全局记忆重启后还在吗？**
A: 在。记忆保存在 `C:\Users\DELL\.claude\global-memory\memory.md`，是普通文本文件，不会因重启丢失。

**Q: 如何备份工具箱？**
A: 复制 `F:\Toolbox` 目录即可。API Key 在 `.env` 文件中，记忆文件在 `~/.claude/global-memory/` 中。
