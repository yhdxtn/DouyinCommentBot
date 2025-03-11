import subprocess

# 获取连接的设备列表
def get_connected_devices():
    result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    
    # 解析 adb devices 的输出
    lines = output.splitlines()
    devices = []
    
    # 跳过第一行标题，并获取每个设备的序列号
    for line in lines[1:]:
        if line.strip():
            device_id = line.split()[0]
            devices.append(device_id)
    
    return devices

# 显示设备并让用户选择
def select_device(devices):
    if not devices:
        print("没有连接任何设备。")
        return None
    
    # 显示设备列表
    print("已连接的设备：")
    for idx, device in enumerate(devices, start=1):
        print(f"{idx}. {device}")
    
    # 用户选择设备
    try:
        choice = int(input(f"请输入设备编号（1 到 {len(devices)}）："))
        if 1 <= choice <= len(devices):
            return devices[choice - 1]
        else:
            print(f"无效的选择，请输入一个有效的数字（1 到 {len(devices)}）。")
            return None
    except ValueError:
        print("请输入有效的数字。")
        return None

# 获取用户输入的分辨率
def get_resolution():
    try:
        resolution = int(input("请输入最大分辨率（如 1080，720，1440 等）："))
        return resolution
    except ValueError:
        print("无效的分辨率输入，使用默认分辨率。")
        return None

# 主程序
def main():
    devices = get_connected_devices()
    selected_device = select_device(devices)
    
    if selected_device:
        print(f"你选择的设备是：{selected_device}")
        
        # 获取分辨率
        resolution = get_resolution()
        
        # 构建 scrcpy 命令
        cmd = ['scrcpy', '-s', selected_device]
        
        # 如果提供了分辨率参数，则添加到命令中
        if resolution:
            cmd.append('-m')
            cmd.append(str(resolution))
        
        # 执行 scrcpy 命令
        subprocess.run(cmd)

if __name__ == "__main__":
    main()
