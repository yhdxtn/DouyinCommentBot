import sys
import subprocess
import re
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox

class ADBWirelessManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("ADB 无线连接管理器")
        self.setGeometry(100, 100, 400, 400)
        
        layout = QVBoxLayout()
        
        self.deviceLabel = QLabel("选择设备：")
        layout.addWidget(self.deviceLabel)
        
        self.deviceComboBox = QComboBox()
        layout.addWidget(self.deviceComboBox)
        
        self.refreshButton = QPushButton("刷新设备")
        self.refreshButton.clicked.connect(self.list_devices)
        layout.addWidget(self.refreshButton)
        
        self.connectButton = QPushButton("开启无线连接")
        self.connectButton.clicked.connect(self.connect_wireless)
        layout.addWidget(self.connectButton)
        
        self.disconnectButton = QPushButton("断开无线连接")
        self.disconnectButton.clicked.connect(self.disconnect_wireless)
        layout.addWidget(self.disconnectButton)
        
        self.scrcpyLabel = QLabel("选择 scrcpy 最大分辨率：")
        layout.addWidget(self.scrcpyLabel)
        
        self.scrcpyComboBox = QComboBox()
        self.scrcpyComboBox.addItems(["默认", "640", "800", "1024", "1280", "1920"])
        layout.addWidget(self.scrcpyComboBox)
        
        self.scrcpyButton = QPushButton("启动 scrcpy")
        self.scrcpyButton.clicked.connect(self.start_scrcpy)
        layout.addWidget(self.scrcpyButton)
        
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        layout.addWidget(self.logOutput)
        
        self.setLayout(layout)
        self.list_devices()
    
    def log(self, message):
        self.logOutput.append(message)
    
    def run_command(self, command):
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip()
        except subprocess.CalledProcessError as e:
            return str(e)
    
    def list_devices(self):
        self.deviceComboBox.clear()
        result = self.run_command("adb devices")
        devices = re.findall(r"(\S+)\s+device", result)
        if devices:
            self.deviceComboBox.addItems(devices)
            self.log("设备列表已更新")
        else:
            self.log("未检测到设备")
    
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
        device_id = self.deviceComboBox.currentText()
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
        ip_address = self.get_device_ip(self.deviceComboBox.currentText())
        if ip_address:
            self.log(f"断开 {ip_address}...")
            result = self.run_command(f"adb disconnect {ip_address}:5555")
            self.log(result)
        else:
            self.log("无法找到设备 IP")
    
    def start_scrcpy(self):
        device_id = self.deviceComboBox.currentText()
        if not device_id:
            self.log("请选择设备")
            return
        
        resolution = self.scrcpyComboBox.currentText()
        scrcpy_command = f"scrcpy -s {device_id}"
        if resolution != "默认":
            scrcpy_command += f" -m {resolution}"
        
        self.log(f"启动 scrcpy 连接到 {device_id}，分辨率：{resolution}...")
        subprocess.Popen(scrcpy_command, shell=True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ADBWirelessManager()
    window.show()
    sys.exit(app.exec())