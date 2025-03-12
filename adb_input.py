import time
import os
import threading
import tkinter as tk
from ppadb.client import Client as AdbClient

def connect_to_devices():
    """
    连接到所有 ADB 设备，并返回设备列表
    """
    client = AdbClient(host="127.0.0.1", port=5037)
    devices = client.devices()

    if len(devices) == 0:
        print("没有检测到设备，请检查设备是否连接并启用 USB 调试。")
        exit(1)

    return devices

def get_device_resolution(device):
    """
    获取设备的屏幕分辨率 (宽 x 高)，并处理"Override size"的情况
    """
    size = device.shell("wm size").strip()
    
    # 检查并忽略"Override size"的部分，只获取分辨率数据
    if "Override size" in size:
        resolution = size.split(":")[1].strip().split()[0]
    else:
        resolution = size.split(":")[1].strip()
    
    width, height = map(int, resolution.split("x"))
    return width, height

def calculate_click_position(device, standard_x, standard_y, standard_width, standard_height):
    """
    根据设备的分辨率计算相对的点击坐标
    """
    device_width, device_height = get_device_resolution(device)
    
    # 默认比例计算
    x = int((standard_x / standard_width) * device_width)
    y = int((standard_y / standard_height) * device_height)
    return x, y

def click_on_device(device, standard_x, standard_y, standard_width=720, standard_height=1600):
    """
    在设备上模拟点击，根据设备分辨率动态计算坐标
    """
    x, y = calculate_click_position(device, standard_x, standard_y, standard_width, standard_height)
    device.shell(f"input tap {x} {y}")

def copy_text_to_clipboard(device, text):
    """
    将文本复制到安卓设备的剪贴板
    """
    device.shell(f"am broadcast -a clipper.set -e text \"{text}\"")

def paste_from_clipboard(device):
    """
    模拟粘贴操作
    """
    device.shell("input keyevent 279")  # 粘贴操作

def press_enter_key(device):
    """
    模拟按下回车键
    """
    device.shell("input keyevent 66")  # 回车键

def send_text_to_device(device, user_input_text):
    """
    发送文本到设备，只执行一次
    """
    # 模拟点击 (100, 1450) 坐标
    click_on_device(device, 100, 1450)

    # 复制用户输入的文本到设备剪贴板
    copy_text_to_clipboard(device, user_input_text)

    # 模拟粘贴操作
    paste_from_clipboard(device)

    # 模拟回车提交
    press_enter_key(device)

def send_to_selected_devices(devices, selected_devices, user_input_text):
    """
    在选中的设备上发送文本
    """
    threads = []
    for device in selected_devices:
        thread = threading.Thread(target=send_text_to_device, args=(device, user_input_text))
        threads.append(thread)
        thread.start()

    # 等待所有线程执行完毕
    for thread in threads:
        thread.join()

def on_send_button_click(devices, device_checkboxes, entry_text):
    """
    发送按钮点击事件，处理文本发送
    """
    user_input_text = entry_text.get("1.0", "end-1c")  # 获取多行文本框内容

    if not user_input_text:
        messagebox.showerror("错误", "请输入要发送的文本！")
        return

    selected_devices = [device for device, checkbox in zip(devices, device_checkboxes) if checkbox.get()]
    
    if not selected_devices:
        messagebox.showerror("错误", "请选择至少一个设备！")
        return

    send_to_selected_devices(selected_devices, selected_devices, user_input_text)

def create_gui(devices):
    """
    创建图形界面，供用户选择设备并发送文本
    """
    root = tk.Tk()
    root.title("设备文本发送器")

    # 创建设备选择界面
    device_checkboxes = []
    for i, device in enumerate(devices):
        var = tk.IntVar()
        checkbox = tk.Checkbutton(root, text=f"设备 {device.serial}", variable=var)
        checkbox.grid(row=i, column=0, sticky="w")
        device_checkboxes.append(var)

    # 输入框
    tk.Label(root, text="请输入要发送的文本：").grid(row=len(devices), column=0, sticky="w")
    entry_text = tk.Text(root, width=60, height=5)  # 改用多行文本框
    entry_text.grid(row=len(devices)+1, column=0, pady=10)

    # 发送按钮
    send_button = tk.Button(root, text="发送", command=lambda: on_send_button_click(devices, device_checkboxes, entry_text))
    send_button.grid(row=len(devices)+2, column=0)

    root.mainloop()

def main():
    """
    主函数，连接设备并启动 GUI
    """
    print("正在连接设备...")
    devices = connect_to_devices()

    # 创建并启动图形界面
    create_gui(devices)

if __name__ == "__main__":
    main()
