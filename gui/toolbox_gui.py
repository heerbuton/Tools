"""
Toolbox GUI v3.0 - 电脑维护工具箱
现代设计 + Markdown 渲染 + 全量扫描
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess, threading, json, os, sys, glob, time, shutil, urllib.request, re
from pathlib import Path

# ===== 路径 =====
if getattr(sys, 'frozen', False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).parent
ENV_FILE = ROOT / ".env"
HOME = Path.home()

# ===== API Key =====
API_KEY = ""
# 优先查找 exe 同目录，其次查找上级目录
for env_path in [ENV_FILE, ROOT.parent / ".env"]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip()
        if API_KEY:
            break

# ===== 主题色 =====
T = {
    "bg":       "#0f0f1a",
    "card":     "#1a1a2e",
    "surface":  "#16213e",
    "accent":   "#00d2ff",
    "accent2":  "#7b2ff7",
    "green":    "#00e676",
    "yellow":   "#ffab00",
    "red":      "#ff1744",
    "text":     "#e0e0e0",
    "dim":      "#6b7280",
    "white":    "#ffffff",
    "btn":      "#1e3a5f",
    "btn_h":    "#2a4a7f",
    "input":    "#0d1b2a",
}


class MarkdownRenderer:
    """在 tkinter Text widget 中渲染 Markdown"""

    def __init__(self, text_widget):
        self.tw = text_widget
        self._setup_tags()

    def _setup_tags(self):
        self.tw.tag_configure("h1", font=("Microsoft YaHei UI", 18, "bold"), foreground=T["accent"], spacing3=8)
        self.tw.tag_configure("h2", font=("Microsoft YaHei UI", 14, "bold"), foreground=T["accent2"], spacing3=6)
        self.tw.tag_configure("h3", font=("Microsoft YaHei UI", 12, "bold"), foreground=T["white"], spacing3=4)
        self.tw.tag_configure("bold", font=("Microsoft YaHei UI", 10, "bold"))
        self.tw.tag_configure("code", font=("Consolas", 10), background="#1e1e2e", foreground="#a6e3a1")
        self.tw.tag_configure("bullet", lmargin1=20, lmargin2=30)
        self.tw.tag_configure("green", foreground=T["green"])
        self.tw.tag_configure("yellow", foreground=T["yellow"])
        self.tw.tag_configure("red", foreground=T["red"])
        self.tw.tag_configure("accent", foreground=T["accent"])
        self.tw.tag_configure("dim", foreground=T["dim"])
        self.tw.tag_configure("line", background="#2a2a4a")
        self.tw.tag_configure("card", background=T["card"], lmargin1=10, lmargin2=10, rmargin=10)

    def clear(self):
        self.tw.delete("1.0", "end")

    def render(self, text):
        """渲染 Markdown 文本"""
        self.clear()
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                self.tw.insert("end", "\n")
                continue
            if stripped.startswith("### "):
                self.tw.insert("end", stripped[4:] + "\n", "h3")
            elif stripped.startswith("## "):
                self.tw.insert("end", stripped[3:] + "\n", "h2")
            elif stripped.startswith("# "):
                self.tw.insert("end", stripped[2:] + "\n", "h1")
            elif stripped.startswith("---"):
                self.tw.insert("end", "─" * 60 + "\n", "line")
            elif stripped.startswith("- ") or stripped.startswith("* "):
                self._render_inline("  • " + stripped[2:] + "\n", "bullet")
            elif stripped.startswith("```"):
                continue
            elif stripped.startswith("> "):
                self.tw.insert("end", "  " + stripped[2:] + "\n", "dim")
            else:
                self._render_inline(stripped + "\n")

    def _render_inline(self, text, base_tag=None):
        """处理行内格式（粗体、代码）"""
        parts = re.split(r'(\*\*.*?\*\*|`[^`]+`)', text)
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                self.tw.insert("end", part[2:-2], ("bold", base_tag) if base_tag else ("bold",))
            elif part.startswith("`") and part.endswith("`"):
                self.tw.insert("end", part[1:-1], ("code", base_tag) if base_tag else ("code",))
            else:
                if base_tag:
                    self.tw.insert("end", part, base_tag)
                else:
                    self.tw.insert("end", part)

    def append(self, text, tag=None):
        """直接追加文本（非 Markdown）"""
        self.tw.insert("end", text + "\n", tag or ())

    def append_colored(self, items):
        """追加带颜色的列表 [(text, tag), ...]"""
        for text, tag in items:
            self.tw.insert("end", text + "\n", tag)
        self.tw.see("end")


class ToolBox:
    def __init__(self, root):
        self.root = root
        self.root.title("Toolbox - 电脑维护工具箱")
        self.root.geometry("1024x720")
        self.root.configure(bg=T["bg"])
        self.root.minsize(800, 600)

        self._build_ui()

    def _build_ui(self):
        # ===== 顶部 =====
        hdr = tk.Frame(self.root, bg=T["accent"], height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        inner = tk.Frame(hdr, bg=T["accent"])
        inner.pack(expand=True, fill="both")
        tk.Label(inner, text="⚡ Toolbox", font=("Microsoft YaHei UI", 18, "bold"),
                 bg=T["accent"], fg=T["bg"]).pack(side="left", padx=20)
        tk.Label(inner, text="电脑维护工具箱 v3.0", font=("Microsoft YaHei UI", 10),
                 bg=T["accent"], fg=T["bg"]).pack(side="right", padx=20)

        # ===== 主体 =====
        body = tk.Frame(self.root, bg=T["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=12)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # 左侧面板
        left = tk.Frame(body, bg=T["card"], width=220)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        left.grid_propagate(False)

        tk.Label(left, text="功能", font=("Microsoft YaHei UI", 11, "bold"),
                 bg=T["card"], fg=T["dim"], anchor="w").pack(fill="x", padx=16, pady=(16, 8))

        buttons = [
            ("📊  电脑状态",     self._do_status),
            ("🧹  清理垃圾",     self._do_clean),
            ("💾  磁盘空间",     self._do_disk),
            ("🤖  Claude 缓存",  self._do_claude),
            ("🧠  AI 诊断清理",  self._do_ai),
        ]
        self._buttons = []
        for txt, cmd in buttons:
            b = tk.Button(left, text=txt, font=("Microsoft YaHei UI", 11),
                          bg=T["btn"], fg=T["text"], activebackground=T["btn_h"],
                          activeforeground=T["white"], relief="flat", cursor="hand2",
                          anchor="w", padx=16, pady=10, command=cmd)
            b.pack(fill="x", padx=10, pady=3)
            b.bind("<Enter>", lambda e, b=b: b.configure(bg=T["btn_h"]))
            b.bind("<Leave>", lambda e, b=b: b.configure(bg=T["btn"]))
            self._buttons.append(b)

        # 右侧内容区
        right = tk.Frame(body, bg=T["card"])
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # 标题栏
        self.title_bar = tk.Frame(right, bg=T["surface"], height=44)
        self.title_bar.grid(row=0, column=0, sticky="ew")
        self.title_bar.pack_propagate(False)
        self.title_lbl = tk.Label(self.title_bar, text="就绪", font=("Microsoft YaHei UI", 12, "bold"),
                                   bg=T["surface"], fg=T["accent"], anchor="w")
        self.title_lbl.pack(side="left", padx=16)

        # 内容区（Markdown 渲染）
        content = tk.Frame(right, bg=T["bg"])
        content.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.text = tk.Text(content, font=("Microsoft YaHei UI", 10),
                            bg=T["bg"], fg=T["text"], insertbackground=T["accent"],
                            relief="flat", wrap="word", padx=16, pady=12,
                            selectbackground=T["accent2"], selectforeground=T["white"])
        self.text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(content, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)

        self.md = MarkdownRenderer(self.text)

        # ===== 底部 =====
        bar = tk.Frame(self.root, bg=T["surface"], height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_lbl = tk.Label(bar, text="就绪", font=("Microsoft YaHei UI", 9),
                                    bg=T["surface"], fg=T["dim"], anchor="w", padx=16)
        self.status_lbl.pack(fill="both")

        # 初始内容
        self.md.render("""# 欢迎使用 Toolbox

选择左侧功能开始使用。

## 功能说明

- **电脑状态** — 检测开发工具、服务、磁盘使用率
- **清理垃圾** — 清理日志、临时文件、过时缓存
- **磁盘空间** — 查看各盘使用情况
- **Claude 缓存** — 清理 Claude Code 的缓存文件
- **AI 诊断清理** — DeepSeek V4 Pro 全量扫描 + 智能分级清理

---

> 提示：AI 功能需要配置 DeepSeek API Key（.env 文件）
""")

    # ===== 工具方法 =====

    def _set_title(self, t):
        self.title_lbl.configure(text=t)

    def _set_status(self, t):
        self.status_lbl.configure(text=t)

    def _cmd(self, c):
        try:
            # Windows 上 shell=True 用 cmd.exe，需要显式用 Git Bash
            bash = r"C:\Program Files\Git\bin\bash.exe"
            if os.path.exists(bash):
                r = subprocess.run([bash, "-c", c], capture_output=True, text=True, timeout=60)
            else:
                r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=60)
            return (r.stdout + r.stderr).strip()
        except:
            return ""

    def _parse_disks(self):
        """解析 df 输出，返回 [(drive, total, used, avail, pct, mount), ...]"""
        df_out = self._cmd("df -h 2>/dev/null")
        disks = []
        for line in df_out.split("\n"):
            # 从后往前解析，避免路径中有空格
            # 格式: "C:/Program Files/Git  256G  211G   45G  83% /"
            # 或:   "D:                    220G  160G   61G  73% /d"
            parts = line.split()
            if len(parts) < 6:
                continue
            mount = parts[-1]      # /d or /
            pct_str = parts[-2]    # 73%
            avail = parts[-3]      # 61G
            used = parts[-4]       # 160G
            total = parts[-5]      # 220G
            if not mount.startswith("/"):
                continue
            try:
                pct = int(pct_str.replace("%", ""))
            except:
                continue
            # 挂载点转盘符
            if mount == "/":
                drive = "C:"
            elif len(mount) <= 3:
                drive = mount[1:].upper() + ":"
            else:
                continue
            disks.append((drive, total, used, avail, pct, mount))
        return disks

    # ===== 功能：电脑状态 =====

    def _do_status(self):
        self._set_title("📊 电脑状态")
        self._set_status("正在检测...")

        def work():
            lines = ["# 电脑状态\n"]

            # 开发工具
            lines.append("## 开发工具\n")
            tools = [
                ("Git", "git --version"), ("Node.js", "node --version"),
                ("npm", "npm --version"), ("Python", "python --version"),
                ("Java", "java -version 2>&1"), ("Docker", "docker --version"),
                ("Conda", "conda --version"), ("VS Code", "code --version 2>/dev/null | head -1"),
                ("Bun", "bun --version"), ("Ollama", "ollama --version 2>/dev/null"),
            ]
            for name, cmd in tools:
                out = self._cmd(cmd).split("\n")[0]
                if out and "not found" not in out.lower():
                    lines.append(f"- ✅ **{name}** — `{out}`")
                else:
                    lines.append(f"- ❌ **{name}** — 未安装")
            lines.append("")

            # 服务
            lines.append("## 服务状态\n")
            docker_ok = "Server:" in self._cmd("docker info 2>&1")
            lines.append(f"- {'🟢' if docker_ok else '🔴'} **Docker Engine** — {'运行中' if docker_ok else '未运行'}")
            ollama_ok = bool(self._cmd("curl -s http://localhost:11434/api/tags 2>/dev/null"))
            lines.append(f"- {'🟢' if ollama_ok else '🔴'} **Ollama Server** — {'运行中' if ollama_ok else '未运行'}")
            lines.append("")

            # 磁盘
            lines.append("## 磁盘使用率\n")
            lines.append("| 盘符 | 总容量 | 已用 | 可用 | 使用率 | 状态 |")
            lines.append("|------|--------|------|------|--------|------|")
            for drive, total, used, avail, pct, mount in self._parse_disks():
                if pct >= 90: status = "🔴 危险"
                elif pct >= 75: status = "🟡 注意"
                else: status = "🟢 正常"
                lines.append(f"| {drive} | {total} | {used} | {avail} | {pct}% | {status} |")

            self.root.after(0, lambda: self.md.render("\n".join(lines)))
            self.root.after(0, lambda: self._set_status("检测完成"))

        threading.Thread(target=work, daemon=True).start()

    # ===== 功能：清理垃圾 =====

    def _do_clean(self):
        if not messagebox.askyesno("确认清理", "将清理以下内容：\n\n• PyCharm 错误日志\n• JMeter / Mumu 日志\n• 过时安装脚本\n• 7天前临时文件\n• Claude 缓存\n\n确定继续？"):
            return

        self._set_title("🧹 清理垃圾")
        self._set_status("正在清理...")

        def work():
            lines = ["# 清理结果\n"]
            count = 0

            # 日志
            lines.append("## 日志文件\n")
            for f in glob.glob(str(HOME / "java_error_in_pycharm64_*.log")):
                os.remove(f)
                lines.append(f"- ✅ 已删除 `{Path(f).name}`")
                count += 1
            for name in ["jmeter.log", "mumu_boot.txt", "msfinstall"]:
                p = HOME / name
                if p.exists():
                    os.remove(p)
                    lines.append(f"- ✅ 已删除 `{name}`")
                    count += 1
            lines.append("")

            # Claude 缓存
            lines.append("## Claude 缓存\n")
            for d in ["telemetry", "paste-cache", "shell-snapshots"]:
                p = HOME / ".claude" / d
                if p.exists():
                    files = list(p.iterdir())
                    shutil.rmtree(p, ignore_errors=True)
                    lines.append(f"- ✅ 已清理 `.claude/{d}` ({len(files)} 个文件)")
                    count += 1
            lines.append("")

            # Temp
            lines.append("## 临时文件\n")
            temp_dir = HOME / "AppData" / "Local" / "Temp"
            if temp_dir.exists():
                now = time.time()
                tc = 0
                for f in temp_dir.iterdir():
                    try:
                        if f.is_file() and (now - f.stat().st_mtime) > 7 * 86400:
                            f.unlink()
                            tc += 1
                    except:
                        pass
                if tc:
                    lines.append(f"- ✅ 已清理 {tc} 个 7 天前的临时文件")
                    count += 1
                else:
                    lines.append("- ℹ️ 没有需要清理的临时文件")

            lines.append(f"\n---\n\n**清理完成，共处理 {count} 项**")

            self.root.after(0, lambda: self.md.render("\n".join(lines)))
            self.root.after(0, lambda: self._set_status("清理完成"))

        threading.Thread(target=work, daemon=True).start()

    # ===== 功能：磁盘空间 =====

    def _do_disk(self):
        self._set_title("💾 磁盘空间")
        lines = ["# 磁盘空间\n"]
        lines.append("| 盘符 | 总容量 | 已用 | 可用 | 使用率 | 状态 |")
        lines.append("|------|--------|------|------|--------|------|")
        for drive, total, used, avail, pct, mount in self._parse_disks():
            if pct >= 90: status = "🔴 危险"
            elif pct >= 75: status = "🟡 注意"
            else: status = "🟢 正常"
            lines.append(f"| {drive} | {total} | {used} | {avail} | {pct}% | {status} |")

        lines.append("\n---\n")
        lines.append("> 🔴 红色 = 快满 (>90%)  🟡 黄色 = 注意 (>75%)  🟢 绿色 = 正常")

        self.md.render("\n".join(lines))
        self._set_status("扫描完成")

    # ===== 功能：Claude 缓存 =====

    def _do_claude(self):
        if not messagebox.askyesno("确认", "将清理 Claude 的遥测、快照和粘贴缓存。\n\n确定？"):
            return
        self._set_title("🤖 Claude 缓存")
        lines = ["# Claude 缓存清理\n"]
        for d in ["telemetry", "paste-cache", "shell-snapshots"]:
            p = HOME / ".claude" / d
            if p.exists():
                c = len(list(p.iterdir()))
                shutil.rmtree(p, ignore_errors=True)
                lines.append(f"- ✅ 已清理 `{d}` ({c} 个文件)")
        lines.append("\n---\n\n**清理完成**")
        self.md.render("\n".join(lines))

    # ===== 功能：AI 诊断清理 =====

    def _do_ai(self):
        if not API_KEY:
            messagebox.showerror("错误", "未配置 DeepSeek API Key\n\n请在 F:\\Toolbox\\.env 中设置：\nDEEPSEEK_API_KEY=your_key")
            return
        self._show_disk_selector()

    def _show_disk_selector(self):
        """磁盘选择窗口"""
        win = tk.Toplevel(self.root)
        win.title("选择扫描磁盘")
        win.geometry("400x350")
        win.configure(bg=T["bg"])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="选择要扫描的磁盘", font=("Microsoft YaHei UI", 14, "bold"),
                 bg=T["bg"], fg=T["accent"]).pack(pady=(20, 15))

        # 获取磁盘
        disks = self._parse_disks()

        var = tk.StringVar(value="all")

        frame = tk.Frame(win, bg=T["card"], relief="flat")
        frame.pack(fill="x", padx=20, pady=(0, 15))

        for drive, total, used, avail, pct, mount in disks:
            color = T["red"] if pct >= 90 else (T["yellow"] if pct >= 75 else T["green"])
            f = tk.Frame(frame, bg=T["card"])
            f.pack(fill="x", padx=12, pady=4)
            tk.Radiobutton(f, text="", variable=var, value=drive,
                           bg=T["card"], selectcolor=T["surface"],
                           activebackground=T["card"]).pack(side="left")
            tk.Label(f, text=f"{drive}  {total}  已用 {used}  ({pct}%)",
                     font=("Microsoft YaHei UI", 10), bg=T["card"], fg=color).pack(side="left", padx=8)

        f_all = tk.Frame(frame, bg=T["card"])
        f_all.pack(fill="x", padx=12, pady=(8, 4))
        tk.Radiobutton(f_all, text="", variable=var, value="all",
                       bg=T["card"], selectcolor=T["surface"],
                       activebackground=T["card"]).pack(side="left")
        tk.Label(f_all, text="全部磁盘", font=("Microsoft YaHei UI", 10, "bold"),
                 bg=T["card"], fg=T["accent"]).pack(side="left", padx=8)

        def start():
            win.destroy()
            self._run_ai_scan(var.get())

        tk.Button(win, text="开始扫描", font=("Microsoft YaHei UI", 12, "bold"),
                  bg=T["accent"], fg=T["bg"], relief="flat", cursor="hand2",
                  padx=30, pady=8, command=start).pack(pady=10)

    def _run_ai_scan(self, disk_choice):
        """AI 全量扫描"""
        self._set_title("🧠 AI 诊断清理")
        self._set_status("正在全量扫描...")
        self.md.clear()
        self.md.render("# 正在扫描...\n\n请耐心等待，全量扫描可能需要 1-2 分钟。")

        def work():
            # ===== 全量扫描 =====
            scan_lines = []

            def on_selected_disk(path_str):
                """检查路径是否在选中的磁盘上"""
                if disk_choice == "all":
                    return True
                # Windows: C: D: E: F:
                drive_letter = disk_choice[0].upper()
                return path_str.upper().startswith(drive_letter + ":") or path_str.startswith("/" + drive_letter.lower())

            # 1. 用户目录日志
            for f in HOME.glob("java_error_in_pycharm64_*.log"):
                if on_selected_disk(str(f)):
                    scan_lines.append(f"LOG | {f.name} | {f.stat().st_size//1024}KB | {f}")
            for name in ["jmeter.log", "mumu_boot.txt"]:
                p = HOME / name
                if p.exists() and on_selected_disk(str(p)):
                    scan_lines.append(f"LOG | {name} | {p.stat().st_size//1024}KB | {p}")

            # 2. 过时安装脚本
            for name in ["msfinstall"]:
                p = HOME / name
                if p.exists() and on_selected_disk(str(p)):
                    scan_lines.append(f"SCRIPT | {name} | {p.stat().st_size//1024}KB | {p}")

            # 3. Claude 缓存
            for d_name in ["telemetry", "paste-cache", "shell-snapshots"]:
                d = HOME / ".claude" / d_name
                if d.exists() and on_selected_disk(str(d)):
                    files = [f for f in d.iterdir() if f.is_file()]
                    if files:
                        total = sum(f.stat().st_size for f in files)
                        scan_lines.append(f"CACHE | .claude/{d_name} ({len(files)}个) | {total//1024}KB | {d}")

            # 4. Temp 目录
            temp_dir = HOME / "AppData" / "Local" / "Temp"
            if temp_dir.exists() and on_selected_disk(str(temp_dir)):
                now = time.time()
                old = [f for f in temp_dir.iterdir() if f.is_file() and (now - f.stat().st_mtime) > 7*86400]
                if old:
                    total = sum(f.stat().st_size for f in old)
                    scan_lines.append(f"CACHE | Temp 7天前 ({len(old)}个) | {total//1024}KB | {temp_dir}")

            # 5. 开发缓存（全量）
            dev_caches = [
                ("npm 缓存", HOME / ".npm"),
                ("pip 缓存", HOME / ".cache" / "pip"),
                ("conda 缓存", HOME / ".conda" / "pkgs"),
                ("Gradle 缓存", HOME / ".gradle" / "caches"),
                ("Maven 缓存", HOME / ".m2" / "repository"),
                ("yarn 缓存", HOME / ".cache" / "yarn"),
                ("pnpm 缓存", HOME / ".local" / "share" / "pnpm"),
                ("Cargo 缓存", HOME / ".cargo" / "registry"),
                ("Go 缓存", HOME / "go" / "pkg"),
                (".cache 通用", HOME / ".cache"),
            ]
            for name, path in dev_caches:
                if path.exists() and on_selected_disk(str(path)):
                    try:
                        total = sum(f.stat().st_size for dp, _, files in os.walk(path) for f in [Path(dp) / fn for fn in files] if f.exists())
                        if total > 1024 * 1024:
                            scan_lines.append(f"DEV_CACHE | {name} | {total//(1024*1024)}MB | {path}")
                    except:
                        pass

            # 6. 根目录 node_modules
            nm = HOME / "node_modules"
            if nm.exists() and on_selected_disk(str(nm)):
                try:
                    total = sum(f.stat().st_size for dp, _, files in os.walk(nm) for f in [Path(dp) / fn for fn in files] if f.exists())
                    scan_lines.append(f"DEV_CACHE | 根目录 node_modules | {total//(1024*1024)}MB | {nm}")
                except:
                    pass

            # 7. Docker
            docker_dir = HOME / ".docker"
            if docker_dir.exists() and on_selected_disk(str(docker_dir)):
                try:
                    total = sum(f.stat().st_size for dp, _, files in os.walk(docker_dir) for f in [Path(dp) / fn for fn in files] if f.exists())
                    if total > 1024*1024:
                        scan_lines.append(f"DOCKER | .docker 配置 | {total//(1024*1024)}MB | {docker_dir}")
                except:
                    pass

            # 8. Downloads 安装包
            dl_dir = HOME / "Downloads"
            if dl_dir.exists() and on_selected_disk(str(dl_dir)):
                installers = [(f.name, f.stat().st_size) for f in dl_dir.iterdir()
                              if f.is_file() and f.suffix.lower() in ('.exe', '.msi', '.zip', '.rar', '.7z', '.iso', '.tar.gz')]
                if installers:
                    total = sum(s for _, s in installers)
                    scan_lines.append(f"INSTALLER | Downloads 安装包 ({len(installers)}个) | {total//(1024*1024)}MB | {dl_dir}")

            # 9. 回收站
            recycle = Path("C:/$Recycle.Bin")
            if recycle.exists() and on_selected_disk("C:"):
                try:
                    total = sum(f.stat().st_size for dp, _, files in os.walk(recycle) for f in [Path(dp) / fn for fn in files] if f.exists())
                    if total > 1024*1024:
                        scan_lines.append(f"RECYCLE | 回收站 | {total//(1024*1024)}MB | {recycle}")
                except:
                    pass

            # 10. Windows Update 缓存
            wu_cache = Path("C:/Windows/SoftwareDistribution/Download")
            if wu_cache.exists() and on_selected_disk("C:"):
                try:
                    total = sum(f.stat().st_size for dp, _, files in os.walk(wu_cache) for f in [Path(dp) / fn for fn in files] if f.exists())
                    if total > 1024*1024:
                        scan_lines.append(f"SYSTEM | Windows Update 缓存 | {total//(1024*1024)}MB | {wu_cache}")
                except:
                    pass

            # 11. 浏览器缓存
            browser_caches = [
                ("Chrome 缓存", HOME / "AppData/Local/Google/Chrome/User Data/Default/Cache"),
                ("Edge 缓存", HOME / "AppData/Local/Microsoft/Edge/User Data/Default/Cache"),
                ("Firefox 缓存", HOME / "AppData/Local/Mozilla/Firefox/Profiles"),
            ]
            for name, path in browser_caches:
                if path.exists() and on_selected_disk(str(path)):
                    try:
                        total = sum(f.stat().st_size for dp, _, files in os.walk(path) for f in [Path(dp) / fn for fn in files] if f.exists())
                        if total > 1024*1024:
                            scan_lines.append(f"BROWSER | {name} | {total//(1024*1024)}MB | {path}")
                    except:
                        pass

            # 磁盘信息
            all_disks = self._parse_disks()
            if disk_choice == "all":
                disk_info = "\n".join(f"{d} {t} {u} {a} {p}% {m}" for d, t, u, a, p, m in all_disks)
            else:
                disk_info = "\n".join(f"{d} {t} {u} {a} {p}% {m}" for d, t, u, a, p, m in all_disks if d == disk_choice)

            scan_text = "\n".join(scan_lines) if scan_lines else "未发现可清理项目"

            self.root.after(0, lambda: self._set_status(f"扫描完成，发现 {len(scan_lines)} 类可清理项，正在请求 AI 分析..."))

            # ===== AI 分析 =====
            prompt = f"""你是 Windows 系统存储分析专家。请分析以下数据，给出清理建议。

## 磁盘使用
{disk_info}

## 扫描到的可清理项（类型 | 名称 | 大小 | 路径）
{scan_text}

请按以下 JSON 格式输出（不要输出其他内容）：
{{"summary": "一句话总览", "green": [{{"name": "名称", "size": "大小", "path": "路径", "cmd": "清理命令", "note": "说明"}}], "yellow": [{{"name": "名称", "size": "大小", "path": "路径", "reason": "需判断原因"}}], "red": [{{"name": "名称", "size": "大小", "reason": "不建议原因"}}], "advice": "其他优化建议"}}

规则：
- green: 纯缓存/临时文件/日志，删了不影响功能，必须给出可执行命令
- yellow: 可能有用但占空间，需用户决定
- red: 不建议动
- 命令用 rm -rf / rm -f / find -delete 等
- 大小用"约 XX MB/GB"
- 只输出 JSON"""

            try:
                data = json.dumps({
                    "model": "deepseek-v4-pro",
                    "messages": [
                        {"role": "system", "content": "存储分析专家。只输出JSON。"},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                }, ensure_ascii=False).encode("utf-8")

                req = urllib.request.Request(
                    "https://api.deepseek.com/v1/chat/completions",
                    data=data,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
                )

                with urllib.request.urlopen(req, timeout=180) as resp:
                    r = json.loads(resp.read().decode("utf-8"))
                    content = r["choices"][0]["message"]["content"]

                    m = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    json_str = m.group(1) if m else (re.search(r'\{.*\}', content, re.DOTALL).group(0) if re.search(r'\{.*\}', content, re.DOTALL) else "{}")
                    result = json.loads(json_str)

                    # 渲染 Markdown 报告
                    md_lines = ["# AI 诊断报告\n"]
                    md_lines.append(f"> {result.get('summary', '')}\n")

                    greens = result.get("green", [])
                    yellows = result.get("yellow", [])
                    reds = result.get("red", [])

                    if greens:
                        md_lines.append("## 🟢 可自动清理\n")
                        for i, item in enumerate(greens, 1):
                            md_lines.append(f"### {i}. {item['name']}  ({item['size']})")
                            md_lines.append(f"- 路径: `{item['path']}`")
                            md_lines.append(f"- 命令: `{item.get('cmd', '无')}`")
                            if item.get("note"):
                                md_lines.append(f"- 说明: {item['note']}")
                            md_lines.append("")

                    if yellows:
                        md_lines.append("## 🟡 需要你判断\n")
                        for i, item in enumerate(yellows, 1):
                            md_lines.append(f"### {i}. {item['name']}  ({item['size']})")
                            md_lines.append(f"- 路径: `{item['path']}`")
                            md_lines.append(f"- 原因: {item.get('reason', '')}")
                            md_lines.append("")

                    if reds:
                        md_lines.append("## 🔴 不建议清理\n")
                        for i, item in enumerate(reds, 1):
                            md_lines.append(f"### {i}. {item['name']}  ({item.get('size', '')})")
                            md_lines.append(f"- 原因: {item.get('reason', '')}")
                            md_lines.append("")

                    advice = result.get("advice", "")
                    if advice:
                        md_lines.append("---\n")
                        md_lines.append(f"## 其他建议\n")
                        md_lines.append(advice)

                    self.root.after(0, lambda: self.md.render("\n".join(md_lines)))

                    # 询问清理
                    if greens:
                        self.root.after(200, lambda: self._ask_clean(greens))

                    self.root.after(0, lambda: self._set_status("诊断完成"))

            except Exception as e:
                self.root.after(0, lambda: self.md.render(f"# 请求失败\n\n`{e}`"))
                self.root.after(0, lambda: self._set_status("诊断失败"))

        threading.Thread(target=work, daemon=True).start()

    def _ask_clean(self, greens):
        items = "\n".join(f"  • {it['name']} ({it['size']})" for it in greens)
        if messagebox.askyesno("确认清理", f"将清理以下 🟢 项目：\n\n{items}\n\n确定？"):
            self.md.append("\n---\n\n## 清理结果\n")
            cleaned = 0
            for item in greens:
                path = item.get("path", "")
                cmd = item.get("cmd", "")
                if not (path.startswith(str(HOME)) or path.startswith("/c/Users")):
                    self.md.append(f"- ⏭️ 跳过: {item['name']} (路径不在用户目录)")
                    continue
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                    self.md.append(f"- ✅ 已清理: {item['name']}")
                    cleaned += 1
                except:
                    self.md.append(f"- ❌ 失败: {item['name']}")
            self.md.append(f"\n**清理完成，共 {cleaned} 项**")
            self._set_status("清理完成")


def main():
    root = tk.Tk()
    ToolBox(root)
    root.mainloop()


if __name__ == "__main__":
    main()
