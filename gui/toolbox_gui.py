"""
Toolbox GUI - 电脑维护工具箱可视化版
基于 Python + tkinter
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import json
import os
import sys
import urllib.request

# ===== 配置 =====
SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if hasattr(sys, 'argv') else __file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
HOME = os.path.expanduser("~")

# 加载 API Key
DEEPSEEK_API_KEY = ""
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("DEEPSEEK_API_KEY="):
                DEEPSEEK_API_KEY = line.strip().split("=", 1)[1]

# ===== 颜色主题 =====
COLORS = {
    "bg": "#1e1e2e",
    "fg": "#cdd6f4",
    "accent": "#89b4fa",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "red": "#f38ba8",
    "surface": "#313244",
    "text_bg": "#181825",
    "button": "#45475a",
    "button_hover": "#585b70",
}


class ToolBoxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("电脑维护工具箱 v2.0")
        self.root.geometry("900x650")
        self.root.configure(bg=COLORS["bg"])
        self.root.resizable(True, True)

        # 设置图标（如果存在）
        icon_path = os.path.join(SCRIPT_DIR, "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self._build_ui()

    def _build_ui(self):
        # ===== 顶部标题 =====
        header = tk.Frame(self.root, bg=COLORS["accent"], height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="电脑维护工具箱", font=("Microsoft YaHei UI", 16, "bold"),
                 bg=COLORS["accent"], fg="#1e1e2e").pack(pady=10)

        # ===== 主体区域 =====
        main_frame = tk.Frame(self.root, bg=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧按钮面板
        btn_frame = tk.Frame(main_frame, bg=COLORS["bg"], width=200)
        btn_frame.pack(side="left", fill="y", padx=(0, 10))
        btn_frame.pack_propagate(False)

        buttons = [
            ("📊 查看电脑状态", self.btn_status),
            ("🧹 清理垃圾文件", self.btn_clean),
            ("💾 查看磁盘空间", self.btn_disk),
            ("🤖 清理 Claude 缓存", self.btn_claude_cache),
            ("🧠 AI 智能诊断", self.btn_ai_diagnose),
            ("⚡ AI 智能清理", self.btn_ai_clean),
            ("📝 全局记忆", self.btn_memory),
            ("⚙️ 设置", self.btn_settings),
        ]

        for text, cmd in buttons:
            btn = tk.Button(btn_frame, text=text, font=("Microsoft YaHei UI", 11),
                            bg=COLORS["button"], fg=COLORS["fg"], activebackground=COLORS["button_hover"],
                            activeforeground=COLORS["fg"], relief="flat", cursor="hand2",
                            anchor="w", padx=15, pady=8, command=cmd)
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORS["button_hover"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=COLORS["button"]))

        # 右侧输出区域
        output_frame = tk.Frame(main_frame, bg=COLORS["surface"], relief="flat")
        output_frame.pack(side="right", fill="both", expand=True)

        # 输出标题
        self.output_title = tk.Label(output_frame, text="就绪", font=("Microsoft YaHei UI", 12, "bold"),
                                      bg=COLORS["surface"], fg=COLORS["accent"], anchor="w")
        self.output_title.pack(fill="x", padx=10, pady=(10, 5))

        # 输出文本框
        self.output = scrolledtext.ScrolledText(output_frame, font=("Consolas", 10),
                                                 bg=COLORS["text_bg"], fg=COLORS["fg"],
                                                 insertbackground=COLORS["fg"],
                                                 relief="flat", wrap="word")
        self.output.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 配置文本标签
        self.output.tag_configure("green", foreground=COLORS["green"])
        self.output.tag_configure("yellow", foreground=COLORS["yellow"])
        self.output.tag_configure("red", foreground=COLORS["red"])
        self.output.tag_configure("accent", foreground=COLORS["accent"])
        self.output.tag_configure("bold", font=("Consolas", 10, "bold"))

        # ===== 底部状态栏 =====
        status_bar = tk.Frame(self.root, bg=COLORS["surface"], height=25)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        self.status_label = tk.Label(status_bar, text="就绪", font=("Microsoft YaHei UI", 9),
                                      bg=COLORS["surface"], fg=COLORS["fg"], anchor="w", padx=10)
        self.status_label.pack(fill="both")

    def _set_status(self, text):
        self.status_label.configure(text=text)

    def _set_title(self, text):
        self.output_title.configure(text=text)

    def _clear_output(self):
        self.output.delete("1.0", "end")

    def _append(self, text, tag=None):
        if tag:
            self.output.insert("end", text + "\n", tag)
        else:
            self.output.insert("end", text + "\n")
        self.output.see("end")

    def _run_cmd(self, cmd, callback=None):
        """在后台线程运行命令"""
        def _worker():
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                output = result.stdout + result.stderr
                self.root.after(0, lambda: callback(output) if callback else None)
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self._append("命令超时", "red"))
            except Exception as e:
                self.root.after(0, lambda: self._append(f"错误: {e}", "red"))
        threading.Thread(target=_worker, daemon=True).start()

    def _run_cmd_sync(self, cmd):
        """同步运行命令，返回输出"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return result.stdout + result.stderr
        except Exception as e:
            return f"错误: {e}"

    # ===== 功能按钮 =====

    def btn_status(self):
        self._set_title("📊 电脑状态")
        self._clear_output()
        self._set_status("正在检测...")

        def _work():
            lines = []
            tools = [
                ("Git", "git --version"),
                ("Node.js", "node --version"),
                ("npm", "npm --version"),
                ("Python", "python --version"),
                ("Java", "java -version 2>&1"),
                ("Docker", "docker --version"),
                ("Conda", "conda --version"),
                ("VS Code", "code --version 2>/dev/null | head -1"),
            ]
            self.root.after(0, lambda: self._append("▸ 开发工具", "bold"))
            for name, cmd in tools:
                out = self._run_cmd_sync(cmd).strip().split("\n")[0]
                if out and "not found" not in out and "错误" not in out:
                    self.root.after(0, lambda n=name, o=out: self._append(f"  ✓ {n}  →  {o}", "green"))
                else:
                    self.root.after(0, lambda n=name: self._append(f"  ✗ {n}  →  未安装", "red"))

            # 服务状态
            self.root.after(0, lambda: self._append("\n▸ 服务状态", "bold"))
            docker_ok = "Server:" in self._run_cmd_sync("docker info 2>&1")
            self.root.after(0, lambda: self._append(
                f"  {'●' if docker_ok else '○'} Docker Engine  →  {'运行中' if docker_ok else '未运行'}",
                "green" if docker_ok else "yellow"))
            ollama_ok = "200" in self._run_cmd_sync("curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/api/tags 2>/dev/null")
            self.root.after(0, lambda: self._append(
                f"  {'●' if ollama_ok else '○'} Ollama Server  →  {'运行中' if ollama_ok else '未运行'}",
                "green" if ollama_ok else "yellow"))

            # 磁盘
            self.root.after(0, lambda: self._append("\n▸ 磁盘使用率", "bold"))
            df_out = self._run_cmd_sync("df -h 2>/dev/null | grep -iE '^C:|^D:|^E:|^F:'")
            for line in df_out.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    mount = parts[-1]
                    total, used, avail = parts[1], parts[2], parts[3]
                    pct = parts[4].replace("%", "")
                    tag = "red" if int(pct) >= 90 else ("yellow" if int(pct) >= 75 else "green")
                    self.root.after(0, lambda m=mount, t=total, u=used, a=avail, p=pct, tg=tag:
                                    self._append(f"  {m}  总计 {t}  已用 {u}  可用 {a}  {p}%", tg))

            self.root.after(0, lambda: self._set_status("检测完成"))

        threading.Thread(target=_work, daemon=True).start()

    def btn_clean(self):
        if messagebox.askyesno("确认清理", "将清理以下内容：\n\n• PyCharm 错误日志\n• JMeter 日志\n• 7天前的临时文件\n• 过时安装脚本\n\n确定继续吗？"):
            self._set_title("🧹 清理垃圾文件")
            self._clear_output()
            self._set_status("正在清理...")

            def _work():
                cleaned = 0
                # 日志
                import glob
                for f in glob.glob(os.path.join(HOME, "java_error_in_pycharm64_*.log")):
                    size = os.path.getsize(f)
                    os.remove(f)
                    self.root.after(0, lambda n=os.path.basename(f), s=size: self._append(f"  ✓ 已删除 {n} ({s//1024}KB)", "green"))
                    cleaned += 1

                for name in ["jmeter.log", "mumu_boot.txt", "msfinstall"]:
                    p = os.path.join(HOME, name)
                    if os.path.exists(p):
                        size = os.path.getsize(p)
                        os.remove(p)
                        self.root.after(0, lambda n=name, s=size: self._append(f"  ✓ 已删除 {n} ({s//1024}KB)", "green"))
                        cleaned += 1

                # Claude 缓存
                for d_name in ["paste-cache", "shell-snapshots"]:
                    d = os.path.join(HOME, ".claude", d_name)
                    if os.path.exists(d):
                        import shutil
                        shutil.rmtree(d, ignore_errors=True)
                        self.root.after(0, lambda n=d_name: self._append(f"  ✓ 已清理 .claude/{n}", "green"))
                        cleaned += 1

                # Temp 7天前
                import time, glob as g2
                temp_dir = os.path.join(HOME, "AppData", "Local", "Temp")
                if os.path.exists(temp_dir):
                    now = time.time()
                    count = 0
                    for f in g2.glob(os.path.join(temp_dir, "*")):
                        try:
                            if os.path.isfile(f) and (now - os.path.getmtime(f)) > 7 * 86400:
                                os.remove(f)
                                count += 1
                        except:
                            pass
                    if count > 0:
                        self.root.after(0, lambda c=count: self._append(f"  ✓ 已清理 {c} 个临时文件", "green"))
                        cleaned += 1

                self.root.after(0, lambda: self._append(f"\n清理完成，处理了 {cleaned} 项", "accent"))
                self.root.after(0, lambda: self._set_status("清理完成"))

            threading.Thread(target=_work, daemon=True).start()

    def btn_disk(self):
        self._set_title("💾 磁盘空间")
        self._clear_output()
        self._set_status("正在扫描...")

        def _work():
            df_out = self._run_cmd_sync("df -h 2>/dev/null | grep -iE '^C:|^D:|^E:|^F:'")
            self.root.after(0, lambda: self._append("▸ 分区使用率\n", "bold"))
            self.root.after(0, lambda: self._append(f"  {'盘':<8} {'总容量':<8} {'已用':<8} {'可用':<8} {'使用率'}"))
            self.root.after(0, lambda: self._append("  " + "-" * 50))

            for line in df_out.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    mount = parts[-1]
                    total, used, avail = parts[1], parts[2], parts[3]
                    pct = parts[4].replace("%", "")
                    tag = "red" if int(pct) >= 90 else ("yellow" if int(pct) >= 75 else "green")
                    self.root.after(0, lambda m=mount, t=total, u=used, a=avail, p=pct, tg=tag:
                                    self._append(f"  {m:<8} {t:<8} {u:<8} {a:<8} {p}%", tg))

            self.root.after(0, lambda: self._append("\n  红色=快满(>90%)  黄色=注意(>75%)  绿色=正常", "accent"))
            self.root.after(0, lambda: self._set_status("扫描完成"))

        threading.Thread(target=_work, daemon=True).start()

    def btn_claude_cache(self):
        if messagebox.askyesno("确认清理", "将清理 Claude 的遥测事件、Shell 快照和粘贴缓存。\n\n确定继续吗？"):
            self._set_title("🤖 清理 Claude 缓存")
            self._clear_output()

            for d_name in ["telemetry", "paste-cache", "shell-snapshots"]:
                d = os.path.join(HOME, ".claude", d_name)
                if os.path.exists(d):
                    count = len(os.listdir(d))
                    import shutil
                    shutil.rmtree(d, ignore_errors=True)
                    self._append(f"  ✓ 已清理 {d_name} ({count} 个文件)", "green")

            self._append("\nClaude 缓存清理完成！", "accent")
            self._set_status("清理完成")

    def btn_ai_diagnose(self):
        if not DEEPSEEK_API_KEY:
            messagebox.showerror("错误", "未配置 DeepSeek API Key\n请在 .env 文件中设置 DEEPSEEK_API_KEY")
            return

        self._set_title("🧠 AI 智能诊断")
        self._clear_output()
        self._set_status("正在收集数据并请求 AI 分析...")

        def _work():
            # 收集数据
            self.root.after(0, lambda: self._append("正在收集系统数据...\n"))
            disk_info = self._run_cmd_sync("df -h 2>/dev/null | grep -iE '^C:|^D:|^E:|^F:'")

            dev_lines = []
            for name, cmd in [("Git", "git --version"), ("Node", "node --version"),
                              ("Python", "python --version"), ("Docker", "docker --version")]:
                out = self._run_cmd_sync(cmd).strip().split("\n")[0]
                dev_lines.append(f"{name}: {out if out else '未安装'}")
            dev_info = "\n".join(dev_lines)

            # 调用 AI
            self.root.after(0, lambda: self._append("正在请求 DeepSeek V4 Pro 分析...\n", "accent"))
            prompt = f"""请分析以下 Windows 11 系统状况，给出优化建议：

磁盘：
{disk_info}

开发环境：
{dev_info}

请从以下角度分析：
1. 磁盘空间是否紧张？哪个盘需要重点关注？
2. 开发环境配置是否合理？
3. 有没有其他优化建议？

用简洁的中文回答，给出具体可执行的操作步骤。"""

            try:
                data = json.dumps({
                    "model": "deepseek-v4-pro",
                    "messages": [
                        {"role": "system", "content": "你是专业的系统诊断助手，用简洁的中文回答。"},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": False
                }, ensure_ascii=False).encode("utf-8")

                req = urllib.request.Request(
                    "https://api.deepseek.com/v1/chat/completions",
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                    }
                )

                with urllib.request.urlopen(req, timeout=120) as resp:
                    r = json.loads(resp.read().decode("utf-8"))
                    content = r["choices"][0]["message"]["content"]
                    reasoning = r["choices"][0]["message"].get("reasoning_content", "")

                    if reasoning:
                        self.root.after(0, lambda: self._append("=== 思考过程 ===\n", "accent"))
                        self.root.after(0, lambda: self._append(reasoning))
                        self.root.after(0, lambda: self._append("\n=== 分析结果 ===\n", "accent"))

                    self.root.after(0, lambda: self._append(content))
                    self.root.after(0, lambda: self._set_status("诊断完成"))

            except Exception as e:
                self.root.after(0, lambda: self._append(f"请求失败: {e}", "red"))
                self.root.after(0, lambda: self._set_status("诊断失败"))

        threading.Thread(target=_work, daemon=True).start()

    def btn_ai_clean(self):
        if not DEEPSEEK_API_KEY:
            messagebox.showerror("错误", "未配置 DeepSeek API Key\n请在 .env 文件中设置 DEEPSEEK_API_KEY")
            return

        self._set_title("⚡ AI 智能清理")
        self._clear_output()
        self._set_status("正在扫描...")

        def _work():
            import glob

            # 扫描
            self.root.after(0, lambda: self._append("正在扫描可清理项目...\n", "accent"))

            scan_items = []
            # 日志
            for f in glob.glob(os.path.join(HOME, "java_error_in_pycharm64_*.log")):
                scan_items.append(("LOG", os.path.basename(f), os.path.getsize(f), f))
            for name in ["jmeter.log", "mumu_boot.txt", "msfinstall"]:
                p = os.path.join(HOME, name)
                if os.path.exists(p):
                    scan_items.append(("LOG", name, os.path.getsize(p), p))

            # Claude 缓存
            for d_name in ["telemetry", "paste-cache", "shell-snapshots"]:
                d = os.path.join(HOME, ".claude", d_name)
                if os.path.exists(d):
                    files = os.listdir(d)
                    if files:
                        total = sum(os.path.getsize(os.path.join(d, f)) for f in files if os.path.isfile(os.path.join(d, f)))
                        scan_items.append(("CACHE", f".claude/{d_name} ({len(files)} 个)", total, d))

            # 构造 prompt
            scan_text = "\n".join(f"{t} | {n} | {s//1024}KB | {p}" for t, n, s, p in scan_items)

            self.root.after(0, lambda: self._append("正在请求 AI 分析分级...\n", "accent"))

            prompt = f"""分析以下可清理项目，按三级分类输出JSON：

{scan_text}

输出格式：
{{"green": [{{"name": "名称", "size": "大小", "path": "路径", "cmd": "清理命令"}}], "yellow": [...], "red": [...], "summary": "总览"}}

green=可自动清理(缓存/日志), yellow=需判断, red=不建议动。只输出JSON。"""

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
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                    }
                )

                with urllib.request.urlopen(req, timeout=120) as resp:
                    r = json.loads(resp.read().decode("utf-8"))
                    content = r["choices"][0]["message"]["content"]

                    # 提取 JSON
                    import re
                    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                    else:
                        match = re.search(r'\{.*\}', content, re.DOTALL)
                        json_str = match.group(0) if match else "{}"

                    result = json.loads(json_str)

                    # 展示结果
                    self.root.after(0, lambda: self._append(f"总览：{result.get('summary', '')}\n", "accent"))

                    greens = result.get("green", [])
                    if greens:
                        self.root.after(0, lambda: self._append("🟢 可自动清理：", "green"))
                        for i, item in enumerate(greens, 1):
                            self.root.after(0, lambda i=i, item=item:
                                            self._append(f"  [{i}] {item['name']}  {item['size']}"))

                    yellows = result.get("yellow", [])
                    if yellows:
                        self.root.after(0, lambda: self._append("\n🟡 需要你判断：", "yellow"))
                        for i, item in enumerate(yellows, 1):
                            self.root.after(0, lambda i=i, item=item:
                                            self._append(f"  [{i}] {item['name']}  {item['size']}"))

                    reds = result.get("red", [])
                    if reds:
                        self.root.after(0, lambda: self._append("\n🔴 不建议清理：", "red"))
                        for i, item in enumerate(reds, 1):
                            self.root.after(0, lambda i=i, item=item:
                                            self._append(f"  [{i}] {item['name']}  {item.get('size', '')}"))

                    # 询问是否清理 green 项
                    if greens:
                        self.root.after(100, lambda: self._ask_clean_green(greens))

                    self.root.after(0, lambda: self._set_status("分析完成"))

            except Exception as e:
                self.root.after(0, lambda: self._append(f"请求失败: {e}", "red"))
                self.root.after(0, lambda: self._set_status("分析失败"))

        threading.Thread(target=_work, daemon=True).start()

    def _ask_clean_green(self, greens):
        """询问是否清理 green 项目"""
        items = "\n".join(f"  • {item['name']} ({item['size']})" for item in greens)
        if messagebox.askyesno("确认清理", f"将清理以下 🟢 项目：\n\n{items}\n\n确定继续吗？"):
            self._append("\n正在清理...", "accent")
            cleaned = 0
            for item in greens:
                path = item.get("path", "")
                cmd = item.get("cmd", "")
                if path.startswith(HOME) or path.startswith("/c/Users"):
                    try:
                        subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                        self._append(f"  ✓ 已清理: {item['name']}", "green")
                        cleaned += 1
                    except:
                        self._append(f"  ✗ 失败: {item['name']}", "red")
            self._append(f"\n清理完成，处理了 {cleaned} 项", "accent")

    def btn_memory(self):
        self._set_title("📝 全局记忆")
        self._clear_output()
        mem_file = os.path.join(HOME, ".claude", "global-memory", "memory.md")
        if os.path.exists(mem_file):
            with open(mem_file, "r", encoding="utf-8") as f:
                content = f.read()
            self._append(content)
        else:
            self._append("记忆文件不存在", "yellow")

        self._append("\n" + "=" * 40, "accent")
        self._append("提示：记忆会在 Claude Code 会话中自动加载和保存", "accent")

    def btn_settings(self):
        self._set_title("⚙️ 设置")
        self._clear_output()

        self._append("API 配置", "bold")
        self._append(f"  DeepSeek API Key: {'已配置' if DEEPSEEK_API_KEY else '未配置'}",
                     "green" if DEEPSEEK_API_KEY else "red")
        self._append(f"  配置文件: {ENV_FILE}")
        self._append(f"\n工具箱路径: {SCRIPT_DIR}")
        self._append(f"用户目录: {HOME}")

        self._append("\n" + "=" * 40, "accent")
        self._append("记忆自动触发配置（Claude Code hooks）", "bold")
        hooks_file = os.path.join(HOME, ".claude", "settings.json")
        if os.path.exists(hooks_file):
            with open(hooks_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
            hooks = settings.get("hooks", {})
            if hooks:
                self._append("  ✓ hooks 已配置", "green")
                for event in hooks:
                    self._append(f"    • {event}")
            else:
                self._append("  ✗ hooks 未配置", "red")
        else:
            self._append("  ✗ settings.json 不存在", "red")


def main():
    root = tk.Tk()
    app = ToolBoxGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
