# YOLO 虚拟环境与依赖安装

编号：JKB-005 · 历史验证：已实测 · 最近整理：2026-10-18

## 目标
保留JetPack系统栈，在venv补齐YOLO应用层。
## 已执行
python3.12-venv模拟安装只新增3包，升级/删除0；创建 --system-site-packages 环境。PyTorch使用官方cu132源、固定2.12.0与torchvision0.27.0。
## 成功组合
Ultralytics8.4.179、NumPy1.26.4、opencv-python4.11.0.86、ONNX1.19.1、PySide6 6.12.0。
## 判断
venv能看系统包不等于完全独立；pip提示不卸载环境外包不一定安装失败。CUDA Python依赖可能影响该进程动态库，但不会通过APT替换主机JetPack。
## 复用
环境内使用python -m pip，不加sudo；大安装先--dry-run。NumPy<2为兼容预防，并非已发生ABI报错。
## 代码
requirements/记录历史验证组合，不是所有Jetson版本的通用一键安装器。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

