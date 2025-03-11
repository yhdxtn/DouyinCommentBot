import subprocess
import cv2
import numpy as np
import time
import re

# 1️⃣ 列出连接的 ADB 设备并选择设备
def list_devices():
    try:
        result = subprocess.check_output("adb devices", shell=True).decode()
        devices = result.splitlines()[1:]  # 排除设备列表的标题行
        devices = [device.split()[0] for device in devices if device.strip()]  # 只保留设备ID
        
        if len(devices) == 0:
            print("❌ 没有连接的设备！")
            return None

        print("📱 检测到以下设备：")
        for i, device in enumerate(devices, start=1):
            print(f"{i}. {device}")
        
        # 循环直到用户输入一个有效的设备编号
        while True:
            try:
                choice = int(input(f"请选择要连接的设备（1-{len(devices)}）："))
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

# 2️⃣ 连接到选择的设备并切换到 TCP/IP 模式
def connect_adb(device_id):
    print("🔍 正在获取设备 IP 地址...")
    try:
        result = subprocess.check_output(f"adb -s {device_id} shell ip addr show wlan0", shell=True).decode()
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", result)
        if not match:
            print("❌ 未找到有效的 WiFi IP，请检查设备是否连接到 WiFi")
            return None

        ip_address = match.group(1)
        print(f"📱 手机 WiFi IP 地址: {ip_address}")

        print("🔄 切换到 TCP/IP 模式...")
        subprocess.run(f"adb -s {device_id} tcpip 5555", shell=True)
        time.sleep(2)

        print("🔗 连接到 ADB...")
        subprocess.run(f"adb connect {ip_address}:5555", shell=True)
        time.sleep(2)

        print("✅ ADB 连接成功！")
        return ip_address
    except Exception as e:
        print(f"❌ 连接 ADB 失败: {e}")
        return None

# 3️⃣ 获取手机屏幕分辨率
def get_screen_size(device_id):
    try:
        cmd = f"adb -s {device_id} shell wm size"
        output = subprocess.check_output(cmd, shell=True).decode()
        match = re.search(r"(\d+)x(\d+)", output)
        if match:
            width, height = map(int, match.groups())
            print(f"📱 手机屏幕分辨率: {width}x{height}")
            return width, height
    except Exception as e:
        print(f"❌ 获取屏幕分辨率失败: {e}")
    return None, None

# 4️⃣ 获取 Android 屏幕截图
def get_screenshot(device_id):
    try:
        result = subprocess.run(f"adb -s {device_id} exec-out screencap -p", shell=True, capture_output=True)
        if result.returncode != 0:
            print("❌ 读取安卓截图失败")
            return None
        
        # 解析 PNG 数据
        image_data = np.frombuffer(result.stdout, np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        return image
    except Exception as e:
        print(f"❌ 获取安卓截图失败: {e}")
        return None

# 5️⃣ 监听鼠标点击，并记录坐标
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        screen_width, screen_height = param  # 从 param 获取屏幕分辨率

        # 计算映射到 Android 屏幕的坐标
        x_android = int(x / window_width * screen_width)
        y_android = int(y / window_height * screen_height)

        print(f"🖱️ 点击坐标: PC 窗口内 ({x}, {y}) → 手机屏幕 ({x_android}, {y_android})")

        # 记录到文件
        with open("Coordinate.txt", "a") as file:
            file.write(f"{x_android},{y_android}\n")

        # 发送 ADB 触摸事件
        cmd = f"adb shell input tap {x_android} {y_android}"
        subprocess.run(cmd, shell=True)

# 6️⃣ 运行主程序
def main():
    device_id = list_devices()
    if not device_id:
        return

    ip_address = connect_adb(device_id)
    if not ip_address:
        return

    # 获取并显示截图
    screenshot = get_screenshot(device_id)
    if screenshot is None:
        print("❌ 获取截图失败")
        return

    # 获取截图的尺寸
    global window_width, window_height
    window_height, window_width, _ = screenshot.shape

    # 获取屏幕分辨率
    screen_width, screen_height = get_screen_size(device_id)
    if not screen_width or not screen_height:
        print("⚠️ 无法获取手机屏幕分辨率，点击映射失败")
        return

    # 显示截图并监听鼠标点击
    cv2.namedWindow("scrcpy screen", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("scrcpy screen", mouse_callback, param=(screen_width, screen_height))

    while True:
        # 显示截图
        cv2.imshow("scrcpy screen", screenshot)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    print("🚪 程序已退出")

if __name__ == "__main__":
    main()
