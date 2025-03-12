
# 抖音直播自动评论工具

## 介绍
本项目是一个用于抖音直播自动评论的工具，基于 ADB（Android Debug Bridge）实现。主程序 `adb_click.py` 负责从指定的文本文件 (`.txt`) 中随机选择一行评论，并发送到 Android 设备的剪贴板，再进行自动评论。

## 依赖安装
### 1. 安装 ADB
确保你的计算机上已安装 ADB，如果没有安装，可以参考以下步骤：
- Windows 用户：[下载 ADB](https://developer.android.com/studio/releases/platform-tools) 并解压到某个目录，然后将其添加到环境变量。
- Linux/macOS 用户可以直接使用包管理工具安装：
  ```sh
  sudo apt install adb  # Debian/Ubuntu
  brew install adb      # macOS
  ```

### 2. 安装 `clipper.apk`
`clipper.apk` 用于实现剪贴板功能，在开始使用本工具前，需手动安装并启动它。

```sh
adb install clipper.apk
adb shell am start-service com.koushikdutta.clipboard/.ClipboardService
```
如果无法写入剪贴板，请检查 `clipper.apk` 是否正确安装并启动。
安装模块
```sh
pip install opencv-python numpy ppadb
```
## 文件说明
- `adb_click.py`：主程序，执行自动评论任务。
- `connect.py`：用于无线连接 ADB 设备。
- `SelectDevice.py`：选择连接的设备并启动 `scrcpy` 进行投屏。
- `CoordinateScript.py`：用于获取合适的屏幕坐标。
- `text/`：存放评论内容的 `.txt` 文件。

## 使用方法
1. **连接 ADB 设备**
   - 打开开发者模式，USB调试，并且允许调试
   - 通过 USB 连接设备，运行 `connect.py` 确保设备已连接。

2. **调整屏幕坐标**
   由于不同手机的屏幕分辨率不同，需要修改 `adb_click.py` 里的 `click_on_device(device, 100, 1450)` 为正确的坐标。
   
   - 运行 `python CoordinateScript.py`。
   - 在弹出的窗口中调整缩放比例，点击抖音直播弹幕输入框。
   - 记录弹出的坐标，并替换 `adb_click.py` 中 `click_on_device(device, X, Y)` 的 `X, Y` 值。

3. **开始自动评论**
   - 运行 `python adb_click.py`。
   - 选择要使用的 `.txt` 文件，该文件中的每一行都是一条评论。
   - 程序会随机选择一条评论，复制到剪贴板，并发送到直播弹幕输入框。

## 注意事项
- `clipper.apk` 必须安装并运行，否则无法使用剪贴板功能，只能同一条评论。
- 设备分辨率不同，需要使用 `CoordinateScript.py` 重新获取正确的点击坐标。
- 运行 `adb_click.py` 时请确保设备已连接，并且在抖音直播页面。

## 许可证
本项目仅供学习交流使用，不得用于非法用途。

