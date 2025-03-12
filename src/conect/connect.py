import subprocess
import re
import time

def choose_operation():
    """先选择操作：连接或断联"""
    print("\n请选择操作：")
    print("1. 开启无线连接")
    print("2. 断开无线连接")
    while True:
        op_choice = input("请输入选项 (1 或 2)：").strip()
        if op_choice in ("1", "2"):
            return op_choice
        else:
            print("❌ 请输入有效的选项：1 或 2")

def list_devices():
    """列出所有连接的设备，并让用户选择设备"""
    try:
        result = subprocess.check_output("adb devices", shell=True).decode()
        lines = result.splitlines()[1:]  # 排除第一行标题
        devices = [line.split()[0] for line in lines if line.strip()]
        if not devices:
            print("❌ 没有连接的设备！")
            return None

        print("\n📱 检测到以下设备：")
        for i, device in enumerate(devices, start=1):
            print(f"{i}. {device}")
        
        while True:
            try:
                choice = int(input(f"请选择设备编号（1-{len(devices)}）："))
                if 1 <= choice <= len(devices):
                    selected_device = devices[choice - 1]
                    print(f"✅ 选择的设备：{selected_device}")
                    return selected_device
                else:
                    print(f"❌ 请输入一个有效的设备编号，范围是 1 到 {len(devices)}")
            except ValueError:
                print("❌ 请输入一个有效的数字！")
    except Exception as e:
        print(f"❌ 获取设备列表失败: {e}")
        return None

def enable_tcpip_mode(device_id):
    """将设备切换到 TCP/IP 模式"""
    try:
        subprocess.check_call(f"adb -s {device_id} tcpip 5555", shell=True)
        print(f"🔄 {device_id} 现在处于 TCP/IP 模式")
    except Exception as e:
        print(f"❌ 切换 TCP/IP 模式失败: {e}")

def get_device_ip(device_id):
    """通过 adb shell 命令获取设备 wlan0 接口的 IP 地址"""
    try:
        output = subprocess.check_output(f"adb -s {device_id} shell ip addr show wlan0", shell=True).decode()
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", output)
        if match:
            ip_address = match.group(1)
            return ip_address
        else:
            print("❌ 未找到有效的 WiFi IP，请检查设备是否已连接到 WiFi")
            return None
    except Exception as e:
        print(f"❌ 获取设备 IP 失败: {e}")
        return None

def connect_wireless(ip_address):
    """使用 adb connect 命令通过 IP 地址建立无线连接"""
    try:
        subprocess.check_call(f"adb connect {ip_address}:5555", shell=True)
        print("✅ 无线连接成功！")
    except Exception as e:
        print(f"❌ 无线连接失败: {e}")

def disconnect_wireless(ip_address):
    """使用 adb disconnect 命令断开无线连接"""
    try:
        subprocess.check_call(f"adb disconnect {ip_address}:5555", shell=True)
        print("✅ 无线断开成功！")
    except Exception as e:
        print(f"❌ 无线断开失败: {e}")

def main():
    # 先选择操作
    op_choice = choose_operation()
    
    # 再选择设备
    device_id = list_devices()
    if not device_id:
        return

    # 获取设备的 WiFi IP 地址
    ip_address = get_device_ip(device_id)
    if not ip_address:
        return

    if op_choice == "1":
        # 连接流程
        enable_tcpip_mode(device_id)
        time.sleep(2)  # 等待设备切换模式
        print(f"📱 手机 WiFi IP 地址: {ip_address}")
        connect_wireless(ip_address)
    else:
        # 断联流程
        print(f"📱 手机 WiFi IP 地址: {ip_address}")
        disconnect_wireless(ip_address)

if __name__ == '__main__':
    main()
