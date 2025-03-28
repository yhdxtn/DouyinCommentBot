import sys
import time
import os
import subprocess
import re
import threading
import tkinter as tk
from tkinter import messagebox
from ppadb.client import Client as AdbClient


class ADBWirelessManager:
    def __init__(self, root):
        self.root = root
        self.devices = self.connect_to_devices()
        self.device_checkboxes = []
        self.create_gui()

    def connect_to_devices(self):
        """
        连接到所有 ADB 设备，并返回设备列表
        """
        client = AdbClient(host="127.0.0.1", port=5037)
        devices = client.devices()

        if len(devices) == 0:
            print("没有检测到设备，请检查设备是否连接并启用 USB 调试。")
            exit(1)

        return devices

    def create_gui(self):
        """
        创建图形界面，供用户选择设备并发送文本
        """
        self.root.title("设备管理器")
        
        # 设备选择界面
        tk.Label(self.root, text="选择设备：").grid(row=0, column=0, sticky="w")
        for i, device in enumerate(self.devices):
            var = tk.IntVar()
            checkbox = tk.Checkbutton(self.root, text=f"设备 {device.serial}", variable=var)
            checkbox.grid(row=i+1, column=0, sticky="w")
            self.device_checkboxes.append((device, var))

        # 输入框
        tk.Label(self.root, text="请输入要发送的文本：").grid(row=len(self.devices)+1, column=0, sticky="w")
        self.entry_text = tk.Text(self.root, width=60, height=5)  # 改用多行文本框
        self.entry_text.grid(row=len(self.devices)+2, column=0, pady=10)

        # 发送按钮
        send_button = tk.Button(self.root, text="发送", command=self.on_send_button_click)
        send_button.grid(row=len(self.devices)+3, column=0)

        # ADB无线连接和scrcpy启动控件
        self.deviceComboBox = tk.StringVar()
        self.deviceComboBox.set("请选择设备")
        device_combobox = tk.OptionMenu(self.root, self.deviceComboBox, *[device.serial for device in self.devices])
        device_combobox.grid(row=len(self.devices)+4, column=0, pady=5)

        refresh_button = tk.Button(self.root, text="刷新设备", command=self.list_devices)
        refresh_button.grid(row=len(self.devices)+5, column=0)

        connect_button = tk.Button(self.root, text="开启无线连接", command=self.connect_wireless)
        connect_button.grid(row=len(self.devices)+6, column=0)

        disconnect_button = tk.Button(self.root, text="断开无线连接", command=self.disconnect_wireless)
        disconnect_button.grid(row=len(self.devices)+7, column=0)

        scrcpy_button = tk.Button(self.root, text="启动 scrcpy", command=self.start_scrcpy)
        scrcpy_button.grid(row=len(self.devices)+8, column=0)

        self.logOutput = tk.Text(self.root, width=60, height=5)
        self.logOutput.grid(row=len(self.devices)+9, column=0, pady=5)
        self.logOutput.config(state=tk.DISABLED)

    def log(self, message):
        self.logOutput.config(state=tk.NORMAL)
        self.logOutput.insert(tk.END, message + "\n")
        self.logOutput.config(state=tk.DISABLED)

    def list_devices(self):
        self.deviceComboBox.set("请选择设备")
        self.log("设备列表已更新")
    
    def enable_tcpip_mode(self, device_id):
        self.log(f"切换 {device_id} 到 TCP/IP 模式...")
        self.run_command(f"adb -s {device_id} tcpip 5555")

    def get_device_ip(self, device_id):
        self.log("获取设备 IP 地址...")
        output = self.run_command(f"adb -s {device_id} shell ip addr show wlan0")
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", output)
        if match:
            return match.group(1)
        return None

    def connect_wireless(self):
        device_id = self.deviceComboBox.get()
        if not device_id:
            self.log("请选择设备")
            return
        self.enable_tcpip_mode(device_id)
        threading.Timer(2, self.try_connect, [device_id]).start()

    def try_connect(self, device_id):
        ip_address = self.get_device_ip(device_id)
        if ip_address:
            self.log(f"连接到 {ip_address}...")
            result = self.run_command(f"adb connect {ip_address}:5555")
            self.log(result)
        else:
            self.log("无法获取设备 IP 地址")

    def disconnect_wireless(self):
        device_id = self.deviceComboBox.get()
        ip_address = self.get_device_ip(device_id)
        if ip_address:
            self.log(f"断开 {ip_address}...")
            result = self.run_command(f"adb disconnect {ip_address}:5555")
            self.log(result)
        else:
            self.log("无法找到设备 IP")

    def start_scrcpy(self):
        device_id = self.deviceComboBox.get()
        if not device_id:
            self.log("请选择设备")
            return
        
        scrcpy_command = f"scrcpy -s {device_id}"
        self.log(f"启动 scrcpy 连接到 {device_id}...")
        subprocess.Popen(scrcpy_command, shell=True)

    def run_command(self, command):
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip()
        except subprocess.CalledProcessError as e:
            return str(e)

    def calculate_click_position(self, device, standard_x, standard_y, standard_width=720, standard_height=1600):
        device_width, device_height = self.get_device_resolution(device)
        x = int((standard_x / standard_width) * device_width)
        y = int((standard_y / standard_height) * device_height)
        return x, y

    def get_device_resolution(self, device):
        size = device.shell("wm size").strip()
        if "Override size" in size:
            resolution = size.split(":")[1].strip().split()[0]
        else:
            resolution = size.split(":")[1].strip()
        width, height = map(int, resolution.split("x"))
        return width, height

    def click_on_device(self, device, standard_x, standard_y):
        x, y = self.calculate_click_position(device, standard_x, standard_y)
        device.shell(f"input tap {x} {y}")

    def copy_text_to_clipboard(self, device, text):
        device.shell(f"am broadcast -a clipper.set -e text \"{text}\"")

    def paste_from_clipboard(self, device):
        device.shell("input keyevent 279")

    def press_enter_key(self, device):
        device.shell("input keyevent 66")

    def send_text_to_device(self, device, user_input_text):
        self.click_on_device(device, 100, 1450)
        self.copy_text_to_clipboard(device, user_input_text)
        self.paste_from_clipboard(device)
        self.press_enter_key(device)

    def send_to_selected_devices(self, devices, selected_devices, user_input_text):
        threads = []
        for device in selected_devices:
            thread = threading.Thread(target=self.send_text_to_device, args=(device, user_input_text))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()

    def on_send_button_click(self):
        user_input_text = self.entry_text.get("1.0", "end-1c")
        if not user_input_text:
            messagebox.showerror("错误", "请输入要发送的文本！")
            return
        
        selected_devices = [device for device, checkbox in zip(self.devices, self.device_checkboxes) if checkbox[1].get()]
        if not selected_devices:
            messagebox.showerror("错误", "请选择至少一个设备！")
            return
        
        self.send_to_selected_devices(selected_devices, selected_devices, user_input_text)


def main():
    root = tk.Tk()
    app = ADBWirelessManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
