import random
import time
import os
from ppadb.client import Client as AdbClient

def connect_to_device():
    """
    连接到ADB设备
    """
    client = AdbClient(host="127.0.0.1", port=5037)  # 默认的ADB服务端地址和端口
    devices = client.devices()

    if len(devices) == 0:
        print("没有检测到设备，请检查设备是否连接并启用USB调试。")
        exit(1)
    
    return devices[0]  # 返回连接的第一个设备

def click_on_device(device, x, y):
    """
    在指定的设备上模拟点击 (x, y) 坐标
    """
    print(f"模拟点击: X={x}, Y={y}")
    device.shell(f"input tap {x} {y}")
    print(f"点击事件已发送到设备: X={x}, Y={y}")

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
    print(f"将文本复制到剪贴板: {text}")
    # 使用 ADB 命令通过 clipper.set 将文本复制到剪贴板
    device.shell(f"am broadcast -a clipper.set -e text \"{text}\"")

def paste_from_clipboard(device):
    """
    模拟粘贴操作
    """
    print("模拟粘贴操作")
    # 使用 ADB 命令模拟粘贴
    device.shell("input keyevent 279")  # 粘贴操作的事件ID是279
    print("粘贴操作已发送到设备")

def press_enter_key(device):
    """
    模拟按下回车键
    """
    print("模拟按下回车键 (Enter) 提交输入")
    device.shell("input keyevent 66")  # 按下回车键

def list_text_files():
    """
    列出text目录下所有的txt文件，并显示它们的序号
    """
    text_dir = 'text'
    if not os.path.exists(text_dir):
        print(f"目录 {text_dir} 不存在，请确保该目录存在。")
        exit(1)
    
    txt_files = [f for f in os.listdir(text_dir) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"目录 {text_dir} 下没有找到txt文件。")
        exit(1)
    
    print("可用的文本文件:")
    for i, txt_file in enumerate(txt_files, 1):
        print(f"{i}. {txt_file}")
    
    return txt_files

def main():
    """
    主函数，连接设备并模拟点击、粘贴与提交，每 15 秒循环一次
    """
    print("正在连接到设备...")
    device = connect_to_device()  # 连接到设备
    print(f"已连接设备: {device}")
    
    # 列出所有的txt文件并让用户选择
    txt_files = list_text_files()
    try:
        choice = int(input(f"请输入文件序号 (1-{len(txt_files)}): "))
        if choice < 1 or choice > len(txt_files):
            print("无效的序号。")
            exit(1)
    except ValueError:
        print("输入无效，请输入一个数字。")
        exit(1)
    
    selected_file = txt_files[choice - 1]
    file_path = os.path.join('text', selected_file)
    
    while True:
        # 模拟点击 (300, 2950) 坐标,可用Coordinate测得
        click_on_device(device, 100, 1450)
        
        # 获取所选文件的随机文本
        random_text = get_random_text_from_file(file_path)
        
        # 将文本复制到设备剪贴板
        copy_text_to_clipboard(device, random_text)
        
        # 模拟粘贴操作
        paste_from_clipboard(device)
        
        # 模拟按下回车键提交
        press_enter_key(device)

        # 等待 130 秒后再进行下一次操作
        time.sleep(30)

if __name__ == "__main__":
    main()
