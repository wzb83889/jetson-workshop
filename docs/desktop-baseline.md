# 桌面 Unknown 字段与 NVIDIA 快捷方式

编号：JKB-015 · 历史验证：已实测 · 最近整理：2026-10-18

## 判断
GNOME显卡Unknown/磁盘未知不证明CUDA或存储损坏；交叉检查真实运算、lsblk、包版本和启动状态。
## 已完成
NVIDIA桌面快捷方式可从/etc/skel/Desktop恢复；用户确认已看到。
## 复用
scripts/restore_nvidia_shortcuts.py使用不覆盖现有文件的策略，整理版需验收。
## 边界
原先图标消失和GNOME Unknown的具体根因未完全查明；不能据此重装驱动。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

