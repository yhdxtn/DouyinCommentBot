import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox

class ScrcpyGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("ADB 设备管理")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        
        self.device_label = QLabel("请选择设备:")
        layout.addWidget(self.device_label)
        
        self.device_combo = QComboBox()
        layout.addWidget(self.device_combo)
        
        self.refresh_button = QPushButton("刷新设备列表")
        self.refresh_button.clicked.connect(self.load_devices)
        layout.addWidget(self.refresh_button)
        
        self.resolution_label = QLabel("输入最大分辨率 (可选):")
        layout.addWidget(self.resolution_label)
        
        self.resolution_input = QLineEdit()
        layout.addWidget(self.resolution_input)
        
        self.start_button = QPushButton("启动 scrcpy")
        self.start_button.clicked.connect(self.start_scrcpy)
        layout.addWidget(self.start_button)
        
        self.setLayout(layout)
        self.load_devices()
    
    def load_devices(self):
        self.device_combo.clear()
        devices = self.get_connected_devices()
        if devices:
            self.device_combo.addItems(devices)
        else:
            QMessageBox.warning(self, "提示", "未找到连接的设备！")
    
    def get_connected_devices(self):
        result = subprocess.run(['adb', 'devices'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        lines = output.splitlines()
        devices = [line.split()[0] for line in lines[1:] if line.strip() and 'device' in line]
        return devices
    
    def start_scrcpy(self):
        selected_device = self.device_combo.currentText()
        if not selected_device:
            QMessageBox.warning(self, "错误", "请选择设备！")
            return
        
        resolution = self.resolution_input.text().strip()
        cmd = ['scrcpy', '-s', selected_device]
        
        if resolution.isdigit():
            cmd.extend(['-m', resolution])
        
        subprocess.Popen(cmd)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScrcpyGUI()
    window.show()
    sys.exit(app.exec())
