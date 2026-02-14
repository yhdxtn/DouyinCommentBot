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
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()

    if len(devices) == 0:
        print("没有检测到设备，请检查设备是否连接并启用 USB 调试。")
        exit(1)

    print(f"检测到 {len(devices)} 个设备")
    return devices

def get_device_resolution(device):
    size = device.shell("wm size").strip()
    for line in size.splitlines():
        if "Physical size" in line:
            resolution = line.split(":")[1].strip()
            width, height = map(int, resolution.split("x"))
            return width, height
    raise ValueError(f"无法获取设备 {device.serial} 的分辨率，返回内容：{size}")

def calculate_click_position(device, standard_x, standard_y, standard_width, standard_height):
    device_width, device_height = get_device_resolution(device)

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
        x = int((standard_x / standard_width) * device_width)
        y = int((standard_y / standard_height) * device_height)

    print(f"设备 {device.serial}: 原始坐标 ({standard_x}, {standard_y}) -> 适配后的坐标 ({x}, {y})")
    return x, y

def click_on_device(device, standard_x, standard_y, standard_width=720, standard_height=1600):
    x, y = calculate_click_position(device, standard_x, standard_y, standard_width, standard_height)
    print(f"设备 {device.serial}: 模拟点击 X={x}, Y={y}")
    device.shell(f"input tap {x} {y}")

def get_subtitles_from_srt(filename):
    subtitles = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
            pattern = re.compile(
                r"\d+\s*\n"
                r"(\d{1,2}:\d{2}:\d{2},\d{3})\s*-->\s*"
                r"(\d{1,2}:\d{2}:\d{2},\d{3})\s*\n"
                r"((?:.+\n?)+?)(?=\n{2,}|\Z)",
                re.MULTILINE
            )
            matches = pattern.findall(content)
            for start_time, end_time, text in matches:
                clean_text = " ".join(line.strip() for line in text.strip().splitlines())
                subtitles.append((start_time, clean_text))
    except FileNotFoundError:
        print(f"文件 {filename} 未找到，请确保该文件存在。")
        exit(1)

    return subtitles

def convert_srt_time_to_seconds(srt_time):
    hours, minutes, seconds, milliseconds = map(int, re.split('[:,]', srt_time))
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

def copy_text_to_clipboard(device, text):
    print(f"设备 {device.serial}: 复制文本到剪贴板: {text}")
    device.shell(f'am broadcast -a clipper.set -e text "{text}"')

def paste_from_clipboard(device):
    print(f"设备 {device.serial}: 模拟粘贴操作")
    device.shell("input keyevent 279")

def press_enter_key(device):
    print(f"设备 {device.serial}: 模拟回车键提交输入")
    device.shell("input keyevent 66")

def list_srt_files():
    srt_dir = 'srt'
    if not os.path.exists(srt_dir):
        print(f"目录 {srt_dir} 不存在，请确保该目录存在。")
        exit(1)

    srt_files = [f for f in os.listdir(srt_dir) if f.endswith('.srt')]

    if not srt_files:
        print(f"目录 {srt_dir} 下没有找到 srt 文件。")
        exit(1)

    print("可用的字幕文件:")
    for i, srt_file in enumerate(sorted(srt_files), 1):
        print(f"{i}. {srt_file}")

    return sorted(srt_files)

def controlled_sleep(total_seconds, pause_event, stop_event, step=0.1):
    end = time.time() + max(0.0, total_seconds)
    while time.time() < end:
        if stop_event.is_set():
            return False
        while not pause_event.is_set():
            if stop_event.is_set():
                return False
            time.sleep(0.1)
        time.sleep(min(step, end - time.time()))
    return True

def run_on_device_gui(device, file_path, log_callback, pause_event, stop_event, start_offset_seconds=0.0):
    """
    start_offset_seconds: 跳转起始秒（会跳过小于该秒数的字幕）
    """
    subtitles = get_subtitles_from_srt(file_path)
    if not subtitles:
        log_callback(f"设备 {device.serial}: 字幕为空")
        return

    # 把字幕时间都转成秒，方便跳过
    subs = []
    for start_time, text in subtitles:
        subs.append((convert_srt_time_to_seconds(start_time), text))

    # 跳过 offset 之前的字幕
    subs = [(t, txt) for (t, txt) in subs if t >= start_offset_seconds]
    if not subs:
        log_callback(f"设备 {device.serial}: 起始秒 {start_offset_seconds:.2f}s 之后没有字幕，退出")
        return

    last_time = start_offset_seconds
    log_callback(f"设备 {device.serial}: 开始执行任务（从 {start_offset_seconds:.2f}s 开始），剩余 {len(subs)} 条字幕")

    for target_seconds, text in subs:
        if stop_event.is_set():
            log_callback(f"设备 {device.serial}: 已停止")
            return

        while not pause_event.is_set():
            if stop_event.is_set():
                log_callback(f"设备 {device.serial}: 已停止")
                return
            time.sleep(0.1)

        sleep_time = max(0, target_seconds - last_time)
        if sleep_time > 0:
            log_callback(f"设备 {device.serial}: 等待 {sleep_time:.2f} 秒，目标时间点 {target_seconds:.2f} 秒")
            ok = controlled_sleep(sleep_time, pause_event, stop_event)
            if not ok:
                log_callback(f"设备 {device.serial}: 已停止")
                return
        last_time = target_seconds

        while not pause_event.is_set():
            if stop_event.is_set():
                log_callback(f"设备 {device.serial}: 已停止")
                return
            time.sleep(0.1)

        click_on_device(device, 100, 1450)
        copy_text_to_clipboard(device, text)
        paste_from_clipboard(device)
        press_enter_key(device)
        log_callback(f"设备 {device.serial}: 发送字幕({target_seconds:.2f}s): {text}")

        ok = controlled_sleep(1, pause_event, stop_event)
        if not ok:
            log_callback(f"设备 {device.serial}: 已停止")
            return

    log_callback(f"设备 {device.serial}: 任务完成")

#############################################
#             图形界面相关代码               #
#############################################

class AutomationGUI:
    def __init__(self, master):
        self.master = master
        master.title("SRT 弹幕自动化工具")
        master.geometry("650x600")

        self.pause_event = threading.Event()
        self.pause_event.set()
        self.stop_event = threading.Event()

        # 计时器
        self.timer_running = False
        self.run_start_ts = None
        self.elapsed_before_pause = 0.0

        # ✅ 当前起始偏移（用于显示从多少秒开始）
        self.start_offset_seconds = 0.0

        self.srt_files = list_srt_files()

        self.devices_frame = ttk.Frame(master)
        self.devices_frame.pack(fill="both", padx=10, pady=10)

        self.devices_label = ttk.Label(self.devices_frame, text="已连接设备及字幕选择：")
        self.devices_label.pack(anchor="w")

        self.device_widgets = {}

        btn_frame = ttk.Frame(master)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.load_devices_button = ttk.Button(btn_frame, text="刷新设备", command=self.load_devices)
        self.load_devices_button.pack(side="left", padx=5)

        self.refresh_srt_button = ttk.Button(btn_frame, text="刷新字幕列表", command=self.refresh_srt_files)
        self.refresh_srt_button.pack(side="left", padx=5)

        self.start_button = ttk.Button(btn_frame, text="开始自动化", command=self.start_automation)
        self.start_button.pack(side="left", padx=5)

        self.pause_button = ttk.Button(btn_frame, text="暂停", command=self.toggle_pause)
        self.pause_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(btn_frame, text="停止", command=self.stop_all)
        self.stop_button.pack(side="left", padx=5)

        self.close_button = ttk.Button(btn_frame, text="关闭", command=self.close_app)
        self.close_button.pack(side="right", padx=5)

        # ✅ 起始秒输入（跳转）
        jump_frame = ttk.Frame(master)
        jump_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(jump_frame, text="起始秒(跳转)：").pack(side="left")
        self.offset_var = tk.StringVar(value="0")
        self.offset_entry = ttk.Entry(jump_frame, textvariable=self.offset_var, width=10)
        self.offset_entry.pack(side="left", padx=5)
        ttk.Label(jump_frame, text="例如 20 或 50（仅跳过该秒数之前的字幕）").pack(side="left")

        # 计时显示
        timer_frame = ttk.Frame(master)
        timer_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(timer_frame, text="当前进度：").pack(side="left")
        self.timer_label = ttk.Label(timer_frame, text="0.00 秒")
        self.timer_label.pack(side="left")

        self.log_text = tk.Text(master, wrap="word", height=10)
        self.log_text.pack(expand=True, fill="both", padx=10, pady=10)

        self.load_devices()

        self.master.after(100, self._update_timer_label)
        self.master.protocol("WM_DELETE_WINDOW", self.close_app)

    # -------- 计时器 --------

    def _current_elapsed(self) -> float:
        elapsed = self.elapsed_before_pause
        if self.timer_running and self.run_start_ts is not None:
            elapsed += (time.time() - self.run_start_ts)
        return max(0.0, elapsed)

    def _update_timer_label(self):
        # ✅ 显示“从 offset 起跑”的当前秒
        shown = self.start_offset_seconds + self._current_elapsed()
        self.timer_label.config(text=f"{shown:.2f} 秒")
        self.master.after(100, self._update_timer_label)

    def _timer_start_or_resume(self):
        self.timer_running = True
        self.run_start_ts = time.time()

    def _timer_pause(self):
        if self.timer_running and self.run_start_ts is not None:
            self.elapsed_before_pause += (time.time() - self.run_start_ts)
        self.run_start_ts = None

    def _timer_reset(self):
        self.timer_running = False
        self.run_start_ts = None
        self.elapsed_before_pause = 0.0

    # -------- 字幕/设备 --------

    def refresh_srt_files(self):
        try:
            new_files = list_srt_files()
        except Exception as e:
            messagebox.showerror("错误", f"刷新字幕列表失败: {str(e)}")
            return

        self.srt_files = new_files

        for serial, combo in self.device_widgets.items():
            current = combo.get()
            combo["values"] = self.srt_files
            if current in self.srt_files:
                combo.set(current)
            elif self.srt_files:
                combo.current(0)
            else:
                combo.set("")

        self.log("字幕列表已刷新（仅 srt 文件夹）")

    def load_devices(self):
        for widget in self.devices_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.destroy()
        self.device_widgets.clear()

        try:
            self.devices = connect_to_devices()
        except Exception as e:
            messagebox.showerror("错误", f"连接设备出错: {str(e)}")
            return

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

    # -------- 日志 --------

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    # -------- 控制 --------

    def start_automation(self):
        self.stop_event.clear()

        if not hasattr(self, 'devices') or not self.devices:
            messagebox.showerror("错误", "没有连接到设备！")
            return

        # ✅ 读取起始秒
        try:
            offset = float(self.offset_var.get().strip() or "0")
            if offset < 0:
                raise ValueError("offset < 0")
        except Exception:
            messagebox.showerror("错误", "起始秒请输入非负数字，例如 0 / 20 / 50")
            return

        self.start_offset_seconds = offset

        for device in self.devices:
            serial = device.serial
            if serial not in self.device_widgets:
                continue
            selected_file = self.device_widgets[serial].get()
            if not selected_file:
                messagebox.showerror("错误", f"设备 {serial} 没有选择字幕文件")
                return

        # ✅ 计时从 offset 开始显示，所以内部计时归零
        self._timer_reset()
        self._timer_start_or_resume()

        self.start_button.config(state="disabled")

        for device in self.devices:
            serial = device.serial
            selected_file = self.device_widgets[serial].get()
            subtitle_file = os.path.join('srt', selected_file)

            threading.Thread(
                target=run_on_device_gui,
                args=(device, subtitle_file, self.log, self.pause_event, self.stop_event, offset),
                daemon=True
            ).start()

        self.log(f"所有设备任务已启动（跳转起始秒：{offset:.2f}s）")
        self.start_button.config(state="normal")

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="继续")
            self._timer_pause()
            self.log("已暂停所有设备任务")
        else:
            self.pause_event.set()
            self.pause_button.config(text="暂停")
            self._timer_start_or_resume()
            self.log("已继续所有设备任务")

    def stop_all(self):
        self.stop_event.set()
        self.pause_event.set()
        self.pause_button.config(text="暂停")
        self._timer_pause()
        self.timer_running = False
        self.log("已发送停止指令（所有设备）")

    def close_app(self):
        self.stop_all()
        self.master.destroy()

def main():
    root = tk.Tk()
    app = AutomationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
