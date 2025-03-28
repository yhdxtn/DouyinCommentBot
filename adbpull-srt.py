import random
import time
import os
import threading
import re
import tkinter as tk
from tkinter import ttk, messagebox
from ppadb.client import Client as AdbClient

#############################################
#         设备操作及字幕处理相关函数         #
#############################################

def connect_to_devices():
    """
    连接到所有 ADB 设备，并返回设备列表
    """
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()

    if len(devices) == 0:
        print("没有检测到设备，请检查设备是否连接并启用 USB 调试。")
        exit(1)

    print(f"检测到 {len(devices)} 个设备")
    return devices

def get_device_resolution(device):
    """
    获取设备的屏幕分辨率 (宽 x 高)
    """
    size = device.shell("wm size").strip()
    for line in size.splitlines():
        if "Physical size" in line:
            resolution = line.split(":")[1].strip()
            width, height = map(int, resolution.split("x"))
            return width, height
    raise ValueError(f"无法获取设备 {device.serial} 的分辨率，返回内容：{size}")

def calculate_click_position(device, standard_x, standard_y, standard_width, standard_height):
    """
    根据设备的分辨率计算相对的点击坐标
    """
    device_width, device_height = get_device_resolution(device)
    
    # 针对特定分辨率设备进行调整
    if device_width == 1440 and device_height == 3120:
        x = 300
        y = 3000
    elif device_width == 1096 and device_height == 2560:
        x = 200
        y = 2400
    elif device_width == 720 and device_height == 1560:
        x = 200
        y = 1470 
    elif device_width == 1440 and device_height == 3200:
        x = 433
        y = 2331  
    else:
        # 默认按比例计算
        x = int((standard_x / standard_width) * device_width)
        y = int((standard_y / standard_height) * device_height)

    print(f"设备 {device.serial}: 原始坐标 ({standard_x}, {standard_y}) -> 适配后的坐标 ({x}, {y})")
    return x, y

def click_on_device(device, standard_x, standard_y, standard_width=720, standard_height=1600):
    """
    在设备上模拟点击，根据设备分辨率动态计算坐标
    """
    x, y = calculate_click_position(device, standard_x, standard_y, standard_width, standard_height)
    print(f"设备 {device.serial}: 模拟点击 X={x}, Y={y}")
    device.shell(f"input tap {x} {y}")

def get_subtitles_from_srt(filename):
    """
    从 .srt 文件读取字幕文本，按时间顺序提取
    支持多行字幕（自动拼接为一行）
    """
    subtitles = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            # 匹配字幕块：编号、时间戳、字幕内容（可能多行）
            pattern = re.compile(
                r"\d+\s*\n"                              # 字幕编号
                r"(\d{1,2}:\d{2}:\d{2},\d{3})\s*-->\s*"    # 开始时间
                r"(\d{1,2}:\d{2}:\d{2},\d{3})\s*\n"         # 结束时间（未使用）
                r"((?:.+\n?)+?)(?=\n{2,}|\Z)",             # 字幕内容（支持多行）
                re.MULTILINE
            )
            matches = pattern.findall(content)
            for start_time, end_time, text in matches:
                # 拼接多行字幕为一行，并去除首尾空白
                clean_text = " ".join(line.strip() for line in text.strip().splitlines())
                subtitles.append((start_time, clean_text))
    except FileNotFoundError:
        print(f"文件 {filename} 未找到，请确保该文件存在。")
        exit(1)
    
    return subtitles

def convert_srt_time_to_seconds(srt_time):
    """
    将 .srt 时间字符串 'hh:mm:ss,ms' 转换成秒（float）
    """
    hours, minutes, seconds, milliseconds = map(int, re.split('[:,]', srt_time))
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return total_seconds

def copy_text_to_clipboard(device, text):
    """
    将文本复制到安卓设备的剪贴板
    """
    print(f"设备 {device.serial}: 复制文本到剪贴板: {text}")
    device.shell(f'am broadcast -a clipper.set -e text "{text}"')

def paste_from_clipboard(device):
    """
    模拟粘贴操作
    """
    print(f"设备 {device.serial}: 模拟粘贴操作")
    device.shell("input keyevent 279")  # keyevent 279 表示粘贴操作

def press_enter_key(device):
    """
    模拟按下回车键
    """
    print(f"设备 {device.serial}: 模拟回车键提交输入")
    device.shell("input keyevent 66")  # keyevent 66 表示回车键

def list_srt_files():
    """
    列出 srt 目录下所有的 srt 文件，并显示它们的序号
    """
    srt_dir = 'srt'
    if not os.path.exists(srt_dir):
        print(f"目录 {srt_dir} 不存在，请确保该目录存在。")
        exit(1)

    srt_files = [f for f in os.listdir(srt_dir) if f.endswith('.srt')]

    if not srt_files:
        print(f"目录 {srt_dir} 下没有找到 srt 文件。")
        exit(1)

    print("可用的字幕文件:")
    for i, srt_file in enumerate(srt_files, 1):
        print(f"{i}. {srt_file}")

    return srt_files

def run_on_device_gui(device, file_path, log_callback):
    """
    在设备上执行自动化任务：
    - 按 srt 字幕文件中预设的时间顺序发送文本
    - 每条字幕到达指定时间后执行：点击、复制、粘贴、回车
    log_callback 用于回调更新 GUI 日志
    """
    subtitles = get_subtitles_from_srt(file_path)
    last_time = 0.0

    log_callback(f"设备 {device.serial}: 开始执行任务，共 {len(subtitles)} 条字幕")
    for start_time, text in subtitles:
        target_seconds = convert_srt_time_to_seconds(start_time)
        sleep_time = max(0, target_seconds - last_time)
        if sleep_time > 0:
            log_callback(f"设备 {device.serial}: 等待 {sleep_time:.2f} 秒，目标时间点 {target_seconds:.2f} 秒")
            time.sleep(sleep_time)
        last_time = target_seconds

        click_on_device(device, 100, 1450)
        copy_text_to_clipboard(device, text)
        paste_from_clipboard(device)
        press_enter_key(device)
        log_callback(f"设备 {device.serial}: 发送字幕: {text}")
        time.sleep(1)

#############################################
#             图形界面相关代码               #
#############################################

class AutomationGUI:
    def __init__(self, master):
        self.master = master
        master.title("SRT 弹幕自动化工具")
        master.geometry("600x500")

        # 获取 srt 文件列表（所有设备共用）
        self.srt_files = list_srt_files()

        # 设备列表区
        self.devices_frame = ttk.Frame(master)
        self.devices_frame.pack(fill="both", padx=10, pady=10)
        
        self.devices_label = ttk.Label(self.devices_frame, text="已连接设备及字幕选择：")
        self.devices_label.pack(anchor="w")
        
        # 存放设备对应的下拉框控件，键为设备序列号
        self.device_widgets = {}
        
        # “刷新设备”按钮
        self.load_devices_button = ttk.Button(master, text="刷新设备", command=self.load_devices)
        self.load_devices_button.pack(pady=5)
        
        # 开始自动化按钮
        self.start_button = ttk.Button(master, text="开始自动化", command=self.start_automation)
        self.start_button.pack(pady=10)
        
        # 日志显示框
        self.log_text = tk.Text(master, wrap="word", height=10)
        self.log_text.pack(expand=True, fill="both", padx=10, pady=10)
        
        # 初始加载设备
        self.load_devices()
    
    def load_devices(self):
        # 清空已有设备控件
        for widget in self.devices_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.destroy()
        self.device_widgets.clear()
        
        try:
            self.devices = connect_to_devices()
        except Exception as e:
            messagebox.showerror("错误", f"连接设备出错: {str(e)}")
            return
        
        # 为每个设备创建一行：显示设备序列号和下拉框选择字幕
        for device in self.devices:
            frame = ttk.Frame(self.devices_frame)
            frame.pack(fill="x", pady=2)
            label = ttk.Label(frame, text=f"设备 {device.serial}:")
            label.pack(side="left")
            combo = ttk.Combobox(frame, values=self.srt_files, state="readonly", width=30)
            combo.pack(side="left", padx=5)
            if self.srt_files:
                combo.current(0)
            self.device_widgets[device.serial] = combo
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
    def start_automation(self):
        # 判断是否已连接设备
        if not hasattr(self, 'devices') or not self.devices:
            messagebox.showerror("错误", "没有连接到设备！")
            return
        
        # 检查每个设备是否选择了字幕文件
        for device in self.devices:
            serial = device.serial
            if serial not in self.device_widgets:
                continue
            selected_file = self.device_widgets[serial].get()
            if not selected_file:
                messagebox.showerror("错误", f"设备 {serial} 没有选择字幕文件")
                return
        
        self.start_button.config(state="disabled")
        # 为每个设备启动自动化线程
        for device in self.devices:
            serial = device.serial
            selected_file = self.device_widgets[serial].get()
            subtitle_file = os.path.join('srt', selected_file)
            threading.Thread(target=run_on_device_gui, args=(device, subtitle_file, self.log), daemon=True).start()
        
        self.log("所有设备任务已启动")
        self.start_button.config(state="normal")

def main():
    root = tk.Tk()
    app = AutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
