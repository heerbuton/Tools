"""
Toolbox GUI v2.0 - 电脑维护工具箱可视化版
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import json
import os
import sys
import glob
import time
import shutil
import urllib.request
import re

# ===== 配置 =====
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_FILE = os.path.join(SCRIPT_DIR, ".env")
HOME = os.path.expanduser("~")

DEEPSEEK_API_KEY = ""
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("DEEPSEEK_API_KEY="):
                DEEPSEEK_API_KEY = line.strip().split("=", 1)[1]

# ===== 颜色 =====
C = {
    "bg": "#1e1e2e",
    "fg": "#cdd6f4",
    "accent": "#89b4fa",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "red": "#f38ba8",
    "surface": "#313244",
    "text_bg": "#181825",
    "btn": "#45475a",
    "btn_h": "#585b70",
}


class ToolBox:
    def __init__(self, root):
        self.root = root
        self.root.title("电脑维护工具箱 v2.0")
        self.root.geometry("960x680")
        self.root.configure(bg=C["bg"])

        self._build_header()
        self._build_body()
        self._build_status()

    # ========== UI 构建 ==========

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["accent"], height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="电脑维护工具箱", font=("Microsoft YaHei UI", 15, "bold"),
                 bg=C["accent"], fg="#1e1e2e").pack(expand=True)

    def _build_body(self):
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧按钮
        left = tk.Frame(body, bg=C["bg"], width=190)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        btns = [
            ("查看电脑状态", self._do_status),
            ("清理垃圾文件", self._do_clean),
            ("查看磁盘空间", self._do_disk),
            ("清理 Claude 缓存", self._do_claude),
            ("AI 诊断与清理", self._do_ai),
        ]
        for txt, cmd in btns:
            b = tk.Button(left, text=txt, font=("Microsoft YaHei UI", 11),
                          bg=C["btn"], fg=C["fg"], activebackground=C["btn_h"],
                          activeforeground=C["fg"], relief="flat", cursor="hand2",
                          anchor="w", padx=12, pady=8, command=cmd)
            b.pack(fill="x", pady=2)
            b.bind("<Enter>", lambda e, b=b: b.configure(bg=C["btn_h"]))
            b.bind("<Leave>", lambda e, b=b: b.configure(bg=C["btn"]))

        # 右侧输出
        right = tk.Frame(body, bg=C["surface"])
        right.pack(side="right", fill="both", expand=True)

        self.title_lbl = tk.Label(right, text="就绪", font=("Microsoft YaHei UI", 12, "bold"),
                                   bg=C["surface"], fg=C["accent"], anchor="w")
        self.title_lbl.pack(fill="x", padx=10, pady=(10, 5))

        self.out = scrolledtext.ScrolledText(right, font=("Microsoft YaHei UI", 10),
                                              bg=C["text_bg"], fg=C["fg"],
                                              insertbackground=C["fg"],
                                              relief="flat", wrap="word")
        self.out.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.out.tag_configure("g", foreground=C["green"])
        self.out.tag_configure("y", foreground=C["yellow"])
        self.out.tag_configure("r", foreground=C["red"])
        self.out.tag_configure("a", foreground=C["accent"])
        self.out.tag_configure("b", font=("Microsoft YaHei UI", 10, "bold"))

    def _build_status(self):
        bar = tk.Frame(self.root, bg=C["surface"], height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status = tk.Label(bar, text="就绪", font=("Microsoft YaHei UI", 9),
                                bg=C["surface"], fg=C["fg"], anchor="w", padx=10)
        self.status.pack(fill="both")

    # ========== 工具方法 ==========

    def _set_status(self, t):
        self.status.configure(text=t)

    def _set_title(self, t):
        self.title_lbl.configure(text=t)

    def _clear(self):
        self.out.delete("1.0", "end")

    def _put(self, text, tag=None):
        self.out.insert("end", text + "\n", tag or ())
        self.out.see("end")

    def _cmd(self, c):
        try:
            r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=60)
            return (r.stdout + r.stderr).strip()
        except:
            return ""

    def _disk_menu(self, callback):
        """弹出磁盘选择菜单"""
        win = tk.Toplevel(self.root)
        win.title("选择磁盘")
        win.geometry("320x280")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="选择要扫描的磁盘", font=("Microsoft YaHei UI", 12, "bold"),
                 bg=C["bg"], fg=C["accent"]).pack(pady=(15, 10))

        # 获取磁盘列表 (Windows Git Bash: "D:  220G  160G  61G  73% /d")
        df_out = self._cmd("df -h 2>/dev/null | grep -iE '^[C-F]:'")
        disks = []
        for line in df_out.split("\n"):
            parts = line.split()
            if len(parts) >= 6:
                drive = parts[0]   # D:
                total = parts[1]   # 220G
                avail = parts[3]   # 61G
                pct = parts[4].replace("%", "")  # 73
                disks.append((drive, total, avail, pct))

        var = tk.StringVar(value="all")
        for drive, total, avail, pct in disks:
            tag = f"  ({pct}% 已用, 可用 {avail})"
            tk.Radiobutton(win, text=f"{drive}  总计 {total}{tag}", variable=var, value=drive,
                           font=("Microsoft YaHei UI", 10), bg=C["bg"], fg=C["fg"],
                           selectcolor=C["surface"], activebackground=C["bg"],
                           activeforeground=C["accent"]).pack(anchor="w", padx=30, pady=2)

        tk.Radiobutton(win, text="全部磁盘", variable=var, value="all",
                       font=("Microsoft YaHei UI", 10, "bold"), bg=C["bg"], fg=C["accent"],
                       selectcolor=C["surface"], activebackground=C["bg"]).pack(anchor="w", padx=30, pady=(8, 2))

        def confirm():
            win.destroy()
            callback(var.get())

        tk.Button(win, text="开始扫描", font=("Microsoft YaHei UI", 11),
                  bg=C["accent"], fg="#1e1e2e", relief="flat", cursor="hand2",
                  padx=20, pady=6, command=confirm).pack(pady=15)

    # ========== 功能实现 ==========

    def _do_status(self):
        self._set_title("查看电脑状态")
        self._clear()
        self._set_status("正在检测...")

        def work():
            tools = [
                ("Git", "git --version"),
                ("Node.js", "node --version"),
                ("npm", "npm --version"),
                ("Python", "python --version"),
                ("Java", "java -version 2>&1"),
                ("Docker", "docker --version"),
                ("Conda", "conda --version"),
                ("VS Code", "code --version 2>/dev/null | head -1"),
                ("Bun", "bun --version"),
                ("Ollama", "ollama --version 2>/dev/null"),
            ]
            self.root.after(0, lambda: self._put("开发工具", "b"))
            for name, cmd in tools:
                out = self._cmd(cmd).split("\n")[0]
                if out and "not found" not in out.lower():
                    self.root.after(0, lambda n=name, o=out: self._put(f"  OK {n}  ->  {o}", "g"))
                else:
                    self.root.after(0, lambda n=name: self._put(f"  -- {n}  ->  未安装", "y"))

            self.root.after(0, lambda: self._put(""))
            self.root.after(0, lambda: self._put("服务状态", "b"))
            docker_ok = "Server:" in self._cmd("docker info 2>&1")
            self.root.after(0, lambda: self._put(
                f"  {'运行中' if docker_ok else '未运行'}  Docker Engine", "g" if docker_ok else "y"))
            ollama_ok = self._cmd("curl -s http://localhost:11434/api/tags 2>/dev/null")
            self.root.after(0, lambda: self._put(
                f"  {'运行中' if ollama_ok else '未运行'}  Ollama Server", "g" if ollama_ok else "y"))

            self.root.after(0, lambda: self._put(""))
            self.root.after(0, lambda: self._put("磁盘使用率", "b"))
            df_out = self._cmd("df -h 2>/dev/null | grep -iE '^[C-F]:'")
            for line in df_out.split("\n"):
                parts = line.split()
                if len(parts) >= 6:
                    drive, total, used, avail = parts[0], parts[1], parts[2], parts[3]
                    pct = int(parts[4].replace("%", ""))
                    tag = "r" if pct >= 90 else ("y" if pct >= 75 else "g")
                    self.root.after(0, lambda d=drive, t=total, u=used, a=avail, p=pct, tg=tag:
                                    self._put(f"  {d}  总计 {t}  已用 {u}  可用 {a}  {p}%", tg))

            self.root.after(0, lambda: self._set_status("检测完成"))

        threading.Thread(target=work, daemon=True).start()

    def _do_clean(self):
        if not messagebox.askyesno("确认", "将清理以下内容：\n\n- PyCharm 错误日志\n- JMeter / Mumu 日志\n- 过时安装脚本\n- 7天前临时文件\n- Claude 缓存\n\n确定继续？"):
            return

        self._set_title("清理垃圾文件")
        self._clear()
        self._set_status("正在清理...")

        def work():
            count = 0
            for f in glob.glob(os.path.join(HOME, "java_error_in_pycharm64_*.log")):
                os.remove(f)
                self.root.after(0, lambda n=os.path.basename(f): self._put(f"  已删除 {n}", "g"))
                count += 1

            for name in ["jmeter.log", "mumu_boot.txt", "msfinstall"]:
                p = os.path.join(HOME, name)
                if os.path.exists(p):
                    os.remove(p)
                    self.root.after(0, lambda n=name: self._put(f"  已删除 {n}", "g"))
                    count += 1

            for d in ["paste-cache", "shell-snapshots", "telemetry"]:
                p = os.path.join(HOME, ".claude", d)
                if os.path.exists(p):
                    shutil.rmtree(p, ignore_errors=True)
                    self.root.after(0, lambda n=d: self._put(f"  已清理 .claude/{n}", "g"))
                    count += 1

            temp_dir = os.path.join(HOME, "AppData", "Local", "Temp")
            if os.path.exists(temp_dir):
                now = time.time()
                tc = 0
                for f in glob.glob(os.path.join(temp_dir, "*")):
                    try:
                        if os.path.isfile(f) and (now - os.path.getmtime(f)) > 7 * 86400:
                            os.remove(f)
                            tc += 1
                    except:
                        pass
                if tc:
                    self.root.after(0, lambda c=tc: self._put(f"  已清理 {c} 个临时文件", "g"))
                    count += 1

            self.root.after(0, lambda: self._put(f"\n清理完成，共 {count} 项", "a"))
            self.root.after(0, lambda: self._set_status("清理完成"))

        threading.Thread(target=work, daemon=True).start()

    def _do_disk(self):
        self._set_title("查看磁盘空间")
        self._clear()

        df_out = self._cmd("df -h 2>/dev/null | grep -iE '^C:|^D:|^E:|^F:'")
        self._put("分区使用率\n", "b")
        for line in df_out.split("\n"):
            parts = line.split()
            if len(parts) >= 6:
                drive, total, used, avail = parts[0], parts[1], parts[2], parts[3]
                pct = int(parts[4].replace("%", ""))
                tag = "r" if pct >= 90 else ("y" if pct >= 75 else "g")
                self._put(f"  {drive}  总计 {total}  已用 {used}  可用 {avail}  {pct}%", tag)

        self._put("\n  红色 = 快满 (>90%)  黄色 = 注意 (>75%)  绿色 = 正常", "a")
        self._set_status("扫描完成")

    def _do_claude(self):
        if not messagebox.askyesno("确认", "将清理 Claude 的遥测、快照和粘贴缓存。\n\n确定？"):
            return
        self._set_title("清理 Claude 缓存")
        self._clear()
        for d in ["telemetry", "paste-cache", "shell-snapshots"]:
            p = os.path.join(HOME, ".claude", d)
            if os.path.exists(p):
                c = len(os.listdir(p))
                shutil.rmtree(p, ignore_errors=True)
                self._put(f"  已清理 {d} ({c} 个文件)", "g")
        self._put("\n完成", "a")

    def _do_ai(self):
        if not DEEPSEEK_API_KEY:
            messagebox.showerror("错误", "未配置 DeepSeek API Key\n请在 .env 中设置 DEEPSEEK_API_KEY")
            return
        self._disk_menu(self._run_ai)

    def _run_ai(self, disk_choice):
        self._set_title("AI 诊断与清理")
        self._clear()
        self._set_status("正在扫描...")

        def work():
            # ===== 全量扫描 =====
            self.root.after(0, lambda: self._put("正在扫描系统，请耐心等待...\n", "a"))

            # 磁盘信息
            if disk_choice == "all":
                disk_info = self._cmd("df -h 2>/dev/null | grep -iE '^C:|^D:|^E:|^F:'")
            else:
                disk_info = self._cmd(f"df -h 2>/dev/null | grep -iE '^{disk_choice}'")

            # 开发环境
            dev_lines = []
            for name, cmd in [
                ("Git", "git --version"), ("Node.js", "node --version"),
                ("npm", "npm --version"), ("Python", "python --version"),
                ("Java", "java -version 2>&1"), ("Docker", "docker --version"),
                ("Conda", "conda --version"), ("VS Code", "code --version 2>/dev/null | head -1"),
                ("Bun", "bun --version"), ("Ollama", "ollama --version 2>/dev/null"),
            ]:
                out = self._cmd(cmd).split("\n")[0]
                dev_lines.append(f"{name}: {out if out else '未安装'}")
            dev_info = "\n".join(dev_lines)

            # 扫描可清理项（全量）
            scan_lines = []

            # 1. 用户目录日志
            for f in glob.glob(os.path.join(HOME, "java_error_in_pycharm64_*.log")):
                scan_lines.append(f"LOG | {os.path.basename(f)} | {os.path.getsize(f)//1024}KB | {f}")
            for name in ["jmeter.log", "mumu_boot.txt"]:
                p = os.path.join(HOME, name)
                if os.path.exists(p):
                    scan_lines.append(f"LOG | {name} | {os.path.getsize(p)//1024}KB | {p}")

            # 2. 过时安装脚本
            for name in ["msfinstall"]:
                p = os.path.join(HOME, name)
                if os.path.exists(p):
                    scan_lines.append(f"LOG | {name} | {os.path.getsize(p)//1024}KB | {p}")

            # 3. Claude 缓存
            for d_name in ["telemetry", "paste-cache", "shell-snapshots"]:
                d = os.path.join(HOME, ".claude", d_name)
                if os.path.exists(d):
                    files = [f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
                    if files:
                        total = sum(os.path.getsize(os.path.join(d, f)) for f in files)
                        scan_lines.append(f"CACHE | .claude/{d_name} ({len(files)}个) | {total//1024}KB | {d}")

            # 4. Temp 目录
            temp_dir = os.path.join(HOME, "AppData", "Local", "Temp")
            if os.path.exists(temp_dir):
                now = time.time()
                old_files = []
                for f in glob.glob(os.path.join(temp_dir, "*")):
                    try:
                        if os.path.isfile(f) and (now - os.path.getmtime(f)) > 7 * 86400:
                            old_files.append(f)
                    except:
                        pass
                if old_files:
                    total = sum(os.path.getsize(f) for f in old_files if os.path.isfile(f))
                    scan_lines.append(f"CACHE | Temp 7天前文件 ({len(old_files)}个) | {total//1024}KB | {temp_dir}")

            # 5. npm/pip/conda 缓存
            for name, path in [
                ("npm 缓存", os.path.join(HOME, ".npm")),
                ("pip 缓存", os.path.join(HOME, ".cache", "pip")),
                ("conda 缓存", os.path.join(HOME, ".conda", "pkgs")),
                ("Gradle 缓存", os.path.join(HOME, ".gradle", "caches")),
                ("Maven 缓存", os.path.join(HOME, ".m2", "repository")),
            ]:
                if os.path.exists(path):
                    try:
                        total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, files in os.walk(path) for f in files)
                        if total > 1024 * 1024:  # > 1MB
                            scan_lines.append(f"CACHE | {name} | {total//(1024*1024)}MB | {path}")
                    except:
                        pass

            # 6. 根目录 node_modules
            nm = os.path.join(HOME, "node_modules")
            if os.path.exists(nm):
                try:
                    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, files in os.walk(nm) for f in files)
                    scan_lines.append(f"CACHE | 根目录 node_modules | {total//(1024*1024)}MB | {nm}")
                except:
                    pass

            # 7. Docker 相关
            docker_dir = os.path.join(HOME, ".docker")
            if os.path.exists(docker_dir):
                try:
                    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, files in os.walk(docker_dir) for f in files)
                    if total > 1024 * 1024:
                        scan_lines.append(f"CACHE | .docker 配置/缓存 | {total//(1024*1024)}MB | {docker_dir}")
                except:
                    pass

            # 8. Downloads 中的安装包
            dl_dir = os.path.join(HOME, "Downloads")
            if os.path.exists(dl_dir):
                installers = []
                for f in os.listdir(dl_dir):
                    if f.lower().endswith(('.exe', '.msi', '.zip', '.rar', '.7z', '.iso')):
                        fp = os.path.join(dl_dir, f)
                        if os.path.isfile(fp):
                            installers.append((f, os.path.getsize(fp)))
                if installers:
                    total = sum(s for _, s in installers)
                    scan_lines.append(f"CACHE | Downloads 安装包 ({len(installers)}个) | {total//(1024*1024)}MB | {dl_dir}")

            scan_text = "\n".join(scan_lines) if scan_lines else "未发现可清理项目"

            self.root.after(0, lambda: self._put(f"扫描完成，发现 {len(scan_lines)} 类可清理项\n", "g"))
            self.root.after(0, lambda: self._put("正在请求 AI 分析（可能需要 30-60 秒）...\n", "a"))
            self._set_status("正在请求 DeepSeek V4 Pro 分析...")

            # ===== AI 分析 =====
            prompt = f"""你是 Windows 系统存储分析专家。请分析以下数据，给出清理建议。

## 磁盘使用
{disk_info}

## 开发环境
{dev_info}

## 扫描到的可清理项（类型 | 名称 | 大小 | 路径）
{scan_text}

请按以下 JSON 格式输出（不要输出其他内容）：
{chr(123)}
  "summary": "一句话总览",
  "green": [
    {chr(123)}"name": "名称", "size": "大小", "path": "路径", "cmd": "清理命令", "note": "说明"{chr(125)}
  ],
  "yellow": [
    {chr(123)}"name": "名称", "size": "大小", "path": "路径", "reason": "需判断原因"{chr(125)}
  ],
  "red": [
    {chr(123)}"name": "名称", "size": "大小", "reason": "不建议原因"{chr(125)}
  ],
  "advice": "其他优化建议"
{chr(125)}

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
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                    }
                )

                with urllib.request.urlopen(req, timeout=180) as resp:
                    r = json.loads(resp.read().decode("utf-8"))
                    content = r["choices"][0]["message"]["content"]

                    # 提取 JSON
                    m = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if m:
                        json_str = m.group(1)
                    else:
                        m = re.search(r'\{.*\}', content, re.DOTALL)
                        json_str = m.group(0) if m else "{}"

                    result = json.loads(json_str)

                    # 展示
                    self.root.after(0, lambda: self._put(f"总览：{result.get('summary', '')}\n", "a"))

                    greens = result.get("green", [])
                    yellows = result.get("yellow", [])
                    reds = result.get("red", [])

                    if greens:
                        self.root.after(0, lambda: self._put("可自动清理（安全删除）：", "g"))
                        for i, item in enumerate(greens, 1):
                            self.root.after(0, lambda i=i, it=item:
                                            self._put(f"  [{i}] {it['name']}  {it['size']}"))
                            self.root.after(0, lambda it=item:
                                            self._put(f"       命令: {it.get('cmd', '无')}"))
                            if item.get("note"):
                                self.root.after(0, lambda it=item:
                                                self._put(f"       说明: {it['note']}"))

                    if yellows:
                        self.root.after(0, lambda: self._put("\n需要你判断：", "y"))
                        for i, item in enumerate(yellows, 1):
                            self.root.after(0, lambda i=i, it=item:
                                            self._put(f"  [{i}] {it['name']}  {it['size']}"))
                            self.root.after(0, lambda it=item:
                                            self._put(f"       原因: {it.get('reason', '')}"))

                    if reds:
                        self.root.after(0, lambda: self._put("\n不建议清理：", "r"))
                        for i, item in enumerate(reds, 1):
                            self.root.after(0, lambda i=i, it=item:
                                            self._put(f"  [{i}] {it['name']}  {it.get('size', '')}"))

                    advice = result.get("advice", "")
                    if advice:
                        self.root.after(0, lambda: self._put(f"\n其他建议：{advice}", "a"))

                    # 询问清理
                    if greens:
                        self.root.after(200, lambda: self._ask_clean(greens))
                    else:
                        self.root.after(0, lambda: self._put("\n没有可自动清理的项目", "y"))

                    self.root.after(0, lambda: self._set_status("诊断完成"))

            except Exception as e:
                self.root.after(0, lambda: self._put(f"请求失败: {e}", "r"))
                self.root.after(0, lambda: self._set_status("诊断失败"))

        threading.Thread(target=work, daemon=True).start()

    def _ask_clean(self, greens):
        items = "\n".join(f"  - {it['name']} ({it['size']})" for it in greens)
        if messagebox.askyesno("确认清理", f"将清理以下项目：\n\n{items}\n\n确定？"):
            self._put("\n正在清理...", "a")
            cleaned = 0
            for item in greens:
                path = item.get("path", "")
                cmd = item.get("cmd", "")
                if not (path.startswith(HOME) or path.startswith("/c/Users")):
                    self._put(f"  跳过: {item['name']} (路径不在用户目录)", "y")
                    continue
                try:
                    subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
                    self._put(f"  已清理: {item['name']}", "g")
                    cleaned += 1
                except:
                    self._put(f"  失败: {item['name']}", "r")

            self._put(f"\n清理完成，共 {cleaned} 项", "a")
            self._set_status("清理完成")


def main():
    root = tk.Tk()
    ToolBox(root)
    root.mainloop()


if __name__ == "__main__":
    main()
