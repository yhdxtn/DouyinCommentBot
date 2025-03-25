import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import threading

# 仍然建议设置 LANG 环境变量
os.environ["LANG"] = "en_US.UTF-8"

class ADBTransferTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ADB文件传输工具")
        self.geometry("720x600")
        self.resizable(False, False)
        
        # 操作模式，push：传文件到安卓，pull：从安卓接收
        self.mode = tk.StringVar(value="push")
        
        # 存储设备列表，形式为 {设备号: tk.IntVar()}
        self.devices = {}
        
        # push模式变量
        self.file_path = tk.StringVar()          # 本地待传输文件
        self.target_dir = tk.StringVar(value="/sdcard/")  # 安卓目标目录
        
        # pull模式变量
        self.device_file = tk.StringVar()        # 安卓待拉取的文件或目录（完整路径）
        self.local_dir = tk.StringVar()          # 本地保存目录
        
        self.create_widgets()
        self.refresh_devices()

    def create_widgets(self):
        # 操作模式选择
        mode_frame = tk.Frame(self)
        mode_frame.pack(padx=10, pady=10, fill=tk.X)
        tk.Label(mode_frame, text="操作模式：").pack(side=tk.LEFT)
        tk.Radiobutton(mode_frame, text="发送到安卓", variable=self.mode, value="push", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(mode_frame, text="从安卓接收", variable=self.mode, value="pull", command=self.update_mode).pack(side=tk.LEFT, padx=5)
        
        # 设备选择区域
        dev_frame = tk.Frame(self)
        dev_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(dev_frame, text="可用设备：").pack(side=tk.LEFT)
        self.devices_frame = tk.Frame(dev_frame)
        self.devices_frame.pack(side=tk.LEFT, padx=10)
        tk.Button(dev_frame, text="刷新设备", command=self.refresh_devices).pack(side=tk.LEFT, padx=10)
        
        # push模式控件
        self.push_frame = tk.Frame(self)
        # 本地文件选择
        push_file_frame = tk.Frame(self.push_frame)
        push_file_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(push_file_frame, text="选择文件：").pack(side=tk.LEFT)
        tk.Entry(push_file_frame, textvariable=self.file_path, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(push_file_frame, text="浏览", command=self.select_file).pack(side=tk.LEFT, padx=5)
        # 目标目录选择（安卓目录选择）
        push_target_frame = tk.Frame(self.push_frame)
        push_target_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(push_target_frame, text="目标目录：").pack(side=tk.LEFT)
        self.target_dir_label = tk.Label(push_target_frame, textvariable=self.target_dir, relief="sunken", width=40, anchor="w")
        self.target_dir_label.pack(side=tk.LEFT, padx=5)
        tk.Button(push_target_frame, text="选择目录", command=self.choose_directory).pack(side=tk.LEFT, padx=5)
        
        # pull模式控件
        self.pull_frame = tk.Frame(self)
        # 设备文件选择（支持目录浏览）
        pull_file_frame = tk.Frame(self.pull_frame)
        pull_file_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(pull_file_frame, text="选择安卓文件或目录：").pack(side=tk.LEFT)
        self.device_file_label = tk.Label(pull_file_frame, textvariable=self.device_file, relief="sunken", width=40, anchor="w")
        self.device_file_label.pack(side=tk.LEFT, padx=5)
        tk.Button(pull_file_frame, text="浏览", command=self.choose_device_file).pack(side=tk.LEFT, padx=5)
        # 本地保存目录选择
        pull_local_frame = tk.Frame(self.pull_frame)
        pull_local_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(pull_local_frame, text="保存到目录：").pack(side=tk.LEFT)
        self.local_dir_label = tk.Label(pull_local_frame, textvariable=self.local_dir, relief="sunken", width=40, anchor="w")
        self.local_dir_label.pack(side=tk.LEFT, padx=5)
        tk.Button(pull_local_frame, text="选择目录", command=self.choose_local_directory).pack(side=tk.LEFT, padx=5)
        
        # 默认显示push模式控件
        self.push_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # 传输按钮
        tk.Button(self, text="开始传输", command=self.start_transfer).pack(pady=10)
        
        # 日志框
        log_label = tk.Label(self, text="日志：")
        log_label.pack(anchor=tk.W, padx=10)
        self.log_box = scrolledtext.ScrolledText(self, width=85, height=20, state=tk.DISABLED)
        self.log_box.pack(padx=10, pady=5)
        
    def update_mode(self):
        mode = self.mode.get()
        if mode == "push":
            self.pull_frame.pack_forget()
            self.push_frame.pack(padx=10, pady=5, fill=tk.X)
        elif mode == "pull":
            self.push_frame.pack_forget()
            self.pull_frame.pack(padx=10, pady=5, fill=tk.X)
    
    def log(self, message):
        """在日志框中追加信息"""
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)
    
    def select_file(self):
        """选择待发送的本地文件"""
        file = filedialog.askopenfilename()
        if file:
            self.file_path.set(file)
            self.log(f"选择文件：{file}")
    
    def refresh_devices(self):
        """刷新连接的设备列表"""
        for widget in self.devices_frame.winfo_children():
            widget.destroy()
        self.devices.clear()
        try:
            result = subprocess.run(
                ["adb", "devices"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            output = result.stdout.strip().splitlines()
            if len(output) < 2:
                self.log("未检测到设备。")
                return
            for line in output[1:]:
                if line.strip() == "":
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    device_id = parts[0]
                    var = tk.IntVar()
                    self.devices[device_id] = var
                    chk = tk.Checkbutton(self.devices_frame, text=device_id, variable=var)
                    chk.pack(anchor=tk.W)
            if self.devices:
                self.log(f"检测到设备：{', '.join(self.devices.keys())}")
            else:
                self.log("未检测到有效设备。")
        except Exception as e:
            self.log(f"刷新设备时出错：{e}")
    
    def choose_directory(self):
        """弹出目录选择窗口，从设备获取目录列表供选择（仅限push模式）"""
        selected_devices = [dev for dev, var in self.devices.items() if var.get() == 1]
        if len(selected_devices) != 1:
            messagebox.showwarning("警告", "请选择一个设备来选择目录（请仅勾选一个设备）。")
            return
        device = selected_devices[0]
        popup = tk.Toplevel(self)
        popup.title("选择设备目录")
        popup.geometry("300x400")
        listbox = tk.Listbox(popup)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def fetch_and_update():
            listbox.delete(0, tk.END)
            self.log(f"刷新设备 {device} 的目录列表...")
            try:
                result = subprocess.run(
                    ["adb", "-s", device, "shell", "ls", "-d", "/sdcard/*/"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                output = result.stdout.strip().splitlines()
                if output and output[0] != "":
                    for line in output:
                        listbox.insert(tk.END, line)
                else:
                    listbox.insert(tk.END, "/sdcard/")
            except Exception as e:
                listbox.insert(tk.END, f"错误：{e}")
        
        fetch_and_update()
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="刷新", command=fetch_and_update).pack(side=tk.LEFT, padx=5)
        
        def on_select():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择一个目录")
                return
            dir_selected = listbox.get(selection[0])
            self.target_dir.set(dir_selected)
            self.log(f"选择目标目录：{dir_selected}")
            popup.destroy()
        
        tk.Button(btn_frame, text="确定", command=on_select).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=popup.destroy).pack(side=tk.LEFT, padx=5)
    
    def choose_device_file(self):
        """
        弹出设备文件浏览窗口：
         - 显示当前目录（默认 /sdcard/）下的所有文件和目录；
         - 支持点击“进入目录”按钮进入选中的目录；
         - 支持点击“返回上一级”返回上层目录；
         - “选择”按钮用于确认选择的文件或目录，其完整路径保存到 self.device_file 中。
        """
        selected_devices = [dev for dev, var in self.devices.items() if var.get() == 1]
        if len(selected_devices) != 1:
            messagebox.showwarning("警告", "请选择一个设备来选择文件（请仅勾选一个设备）。")
            return
        device = selected_devices[0]
        popup = tk.Toplevel(self)
        popup.title("选择设备文件")
        popup.geometry("400x500")
        
        # 当前目录变量，初始为 /sdcard/
        current_path = tk.StringVar(value="/sdcard/")
        path_label = tk.Label(popup, textvariable=current_path, relief="sunken")
        path_label.pack(pady=5, fill=tk.X, padx=10)
        
        listbox = tk.Listbox(popup)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        def refresh_files():
            listbox.delete(0, tk.END)
            self.log(f"刷新设备 {device} 的文件列表：{current_path.get()}")
            try:
                cmd = ["adb", "-s", device, "shell", "ls", "-p", current_path.get()]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                output = result.stdout.strip().splitlines()
                if output and output[0] != "":
                    for line in output:
                        listbox.insert(tk.END, line)
                else:
                    listbox.insert(tk.END, "空目录")
            except Exception as e:
                listbox.insert(tk.END, f"错误：{e}")
        
        refresh_files()
        
        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=5)
        
        def go_into():
            """进入选中的目录"""
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择一个目录")
                return
            item = listbox.get(selection[0])
            if not item.endswith("/"):
                messagebox.showwarning("警告", "选择的不是目录")
                return
            # 构造新路径
            base = current_path.get()
            if not base.endswith("/"):
                base += "/"
            new_path = base + item
            current_path.set(new_path)
            refresh_files()
        
        def go_back():
            """返回上一级目录"""
            path = current_path.get().rstrip("/")
            if path == "/sdcard":
                messagebox.showinfo("提示", "已经是根目录")
                return
            parts = path.split("/")[:-1]
            new_path = "/".join(parts)
            if new_path == "":
                new_path = "/"
            else:
                new_path += "/"
            current_path.set(new_path)
            refresh_files()
        
        def select_item():
            """选择当前选中的文件或目录，保存完整路径"""
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择一个文件或目录")
                return
            item = listbox.get(selection[0])
            base = current_path.get()
            if not base.endswith("/"):
                base += "/"
            chosen = base + item
            self.device_file.set(chosen)
            self.log(f"选择设备文件：{chosen}")
            popup.destroy()
        
        tk.Button(btn_frame, text="进入目录", command=go_into).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="返回上一级", command=go_back).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="选择", command=select_item).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="刷新", command=refresh_files).pack(side=tk.LEFT, padx=5)
    
    def choose_local_directory(self):
        """选择本地保存目录（pull模式）"""
        local_dir = filedialog.askdirectory()
        if local_dir:
            self.local_dir.set(local_dir)
            self.log(f"选择本地保存目录：{local_dir}")
    
    def start_transfer(self):
        mode = self.mode.get()
        if mode == "push":
            file = self.file_path.get().strip()
            target = self.target_dir.get().strip()
            if not file:
                messagebox.showwarning("提示", "请选择要传输的文件。")
                return
            if not target:
                messagebox.showwarning("提示", "目标目录不能为空。")
                return
            selected_devices = [dev for dev, var in self.devices.items() if var.get() == 1]
            if not selected_devices:
                messagebox.showwarning("提示", "请选择要传输的设备。")
                return
            threading.Thread(target=self.transfer_push, args=(file, target, selected_devices), daemon=True).start()
        elif mode == "pull":
            device_file = self.device_file.get().strip()
            local_dir = self.local_dir.get().strip()
            if not device_file:
                messagebox.showwarning("提示", "请选择设备上的文件或目录。")
                return
            if not local_dir:
                messagebox.showwarning("提示", "请选择本地保存目录。")
                return
            selected_devices = [dev for dev, var in self.devices.items() if var.get() == 1]
            if not selected_devices:
                messagebox.showwarning("提示", "请选择设备。")
                return
            threading.Thread(target=self.transfer_pull, args=(device_file, local_dir, selected_devices), daemon=True).start()
    
    def transfer_push(self, file, target, devices):
     for device in devices:
        # 如果目标目录以斜杠结尾，附加文件名
        if target.endswith("/"):
            remote_target = target.rstrip("/") + "/" + os.path.basename(file)
        else:
            remote_target = target
        
        self.log(f"开始向设备 {device} 传输文件到 {remote_target} ...")
        cmd = ["adb", "-s", device, "push", file, remote_target]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            stdout, stderr = process.communicate()
            if stdout:
                self.log(f"[{device}] 输出：{stdout.strip()}")
            if stderr:
                self.log(f"[{device}] 错误：{stderr.strip()}")
            if process.returncode == 0:
                self.log(f"[{device}] 文件传输成功。")
            else:
                self.log(f"[{device}] 文件传输失败，返回码：{process.returncode}")
        except Exception as e:
            self.log(f"[{device}] 执行传输时出错：{e}")

    
    def transfer_pull(self, device_file, local_dir, devices):
        """
        对选中的每个设备执行拉取操作：
         - 如果拉取的是单个文件（device_file不以 "/" 结尾）且文件名包含非ASCII字符，
           则使用 adb exec-out cat 的方式读取文件内容，再写入本地文件；
         - 否则调用 adb pull。
        """
        for device in devices:
            basename = os.path.basename(device_file.rstrip("/"))
            # 判断是否为单个文件且文件名中存在非ASCII字符
            if (not device_file.endswith("/")) and any(ord(c) > 127 for c in basename):
                self.log(f"设备 {device} 的文件名包含非ASCII字符，尝试使用 exec-out cat 方式拉取文件。")
                local_path = os.path.join(local_dir, basename)
                try:
                    with open(local_path, "wb") as f:
                        p = subprocess.Popen(
                            ["adb", "-s", device, "exec-out", "cat", device_file],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        stdout, stderr = p.communicate()
                        if stderr:
                            err = stderr.decode("utf-8", errors="replace").strip()
                            self.log(f"[{device}] 错误：{err}")
                        if p.returncode == 0:
                            f.write(stdout)
                            self.log(f"[{device}] 文件拉取成功，保存为 {local_path}")
                        else:
                            self.log(f"[{device}] 文件拉取失败，返回码：{p.returncode}")
                except Exception as e:
                    self.log(f"[{device}] 执行拉取时出错：{e}")
            else:
                self.log(f"开始从设备 {device} 拉取 {device_file} 到 {local_dir} ...")
                cmd = ["adb", "-s", device, "pull", device_file, local_dir]
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                        errors="replace"
                    )
                    stdout, stderr = process.communicate()
                    if stdout:
                        self.log(f"[{device}] 输出：{stdout.strip()}")
                    if stderr:
                        self.log(f"[{device}] 错误：{stderr.strip()}")
                    if process.returncode == 0:
                        self.log(f"[{device}] 文件拉取成功。")
                    else:
                        self.log(f"[{device}] 文件拉取失败，返回码：{process.returncode}")
                except Exception as e:
                    self.log(f"[{device}] 执行拉取时出错：{e}")

    # ... 其它代码保持不变 ...

if __name__ == "__main__":
    app = ADBTransferTool()
    app.mainloop()
