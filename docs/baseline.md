# 设备与软件基准：Orin Nano 8GB

编号：JKB-001 · 历史验证：已实测 · 最近整理：2026-10-18

## 结论
本机为 Jetson Orin Nano 8GB，架构 aarch64、GPU CC 8.7。历史成功组合为 JetPack 7.2.1 / L4T R39.2.1、CUDA 13.2、TensorRT 10.16.2.10。
## 已有证据
- Python 3.12.3；系统可见内存约 7.3GiB；系统盘为 128GB microSD。
- 2026-10-17安装前：根分区116G，已用39G、可用71G；内存可用5.3Gi，swap 0。
- 系统/用户Python环境分开记录。NumPy 1.26.4由系统dist-packages提供；venv内cv2为4.11.0。
## 使用
运行 scripts/inspect_jetson.sh，保留版本和包状态。资源快照不是当前实时状态。
## 边界
电源15W、25W、MAXN_SUPER此前已逐项测试；本次YOLO测速未同步采集电源/温度/频率，不能当作严格25W基准。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

