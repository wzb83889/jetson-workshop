# APT 修复：安装介质源与未加载的 .orig

编号：JKB-002 · 历史验证：已实测 · 最近整理：2026-10-18

## 现象与定位
APT报 file:/tmp/cdrom 没有Release；修复后只有NVIDIA源而无Ubuntu源。
## 判断
磁盘上能搜到源地址不代表APT加载了它。.orig文件是备份；APT加载有效.list/.sources。
## 有效过程
1. 找到并备份sources配置，注释失效file源。
2. 确认Ubuntu Noble arm64源使用ports.ubuntu.com/ubuntu-ports。
3. 将正确deb822配置放到有效.sources文件。
4. apt update无错误后模拟安装目标包，再正式安装。
## 复用边界
历史sed第32行是本机当次文件行号，不可照搬。不要一键覆盖已有源。完整系统维护升级脚本尚未从另会话取回和验收。
## 来源
原台账第4、5、7节；本次不默认执行apt upgrade或autoremove。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

