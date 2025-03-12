import random
import time
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

    print(f"检测到 {len(devices)} 个设备")
    return devices

def get_device_resolution(device):
    """
    获取设备的屏幕分辨率 (宽 x 高)
    """
    size = device.shell("wm size").strip()
    resolution = size.split(":")[1].strip()
    width, height = map(int, resolution.split("x"))
    return width, height

def calculate_click_position(device, standard_x, standard_y, standard_width, standard_height):
    """
    根据设备的分辨率计算相对的点击坐标
    """
    device_width, device_height = get_device_resolution(device)
    
    # 处理特定分辨率设备
    if device_width == 1440 and device_height == 3120:
        x = 300
        y = 3000
    elif device_width == 1096 and device_height == 2560:
        x = 200
        y = 2400
    elif device_width == 720 and device_height == 1560:
        x = 200
        y = 1470  
    else:
        # 默认比例计算
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

def get_random_text_from_file(filename):
    """
    从文件中随机读取一行文本
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return random.choice(lines).strip()  # 返回随机选择的一行并去除两端空白字符
    except FileNotFoundError:
        print(f"文件 {filename} 未找到，请确保该文件存在。")
        exit(1)

def copy_text_to_clipboard(device, text):
    """
    将文本复制到安卓设备的剪贴板
    """
    print(f"设备 {device.serial}: 复制文本到剪贴板: {text}")
    device.shell(f"am broadcast -a clipper.set -e text \"{text}\"")

def paste_from_clipboard(device):
    """
    模拟粘贴操作
    """
    print(f"设备 {device.serial}: 模拟粘贴操作")
    device.shell("input keyevent 279")  # 粘贴操作

def press_enter_key(device):
    """
    模拟按下回车键
    """
    print(f"设备 {device.serial}: 模拟回车键提交输入")
    device.shell("input keyevent 66")  # 回车键

def main():
    """
    主函数，连接设备并模拟点击、粘贴与提交，每 15 秒循环一次
    """
    print("正在连接到设备...")
    device = connect_to_device()  # 连接到设备
    print(f"已连接设备: {device}")
    
    while True:
        # 模拟点击 (300, 2950) 坐标
        click_on_device(device, 300, 2950)
        
        # 获取同目录下的 text.txt 中的随机一行文本
        random_text = get_random_text_from_file('text.txt')
        
        # 将文本复制到设备剪贴板
        copy_text_to_clipboard(device, random_text)

        # 模拟粘贴操作
        paste_from_clipboard(device)

        # 模拟回车提交
        press_enter_key(device)

        # 等待 15 秒后再进行下一次操作
        time.sleep(20)

if __name__ == "__main__":
    main()
