# Qt 无窗口：SSH 与 Wayland 桌面会话

编号：JKB-009 · 历史验证：已实测 · 最近整理：2026-10-18

## 排查
TTY中DISPLAY/WAYLAND均空；timeout20s导入测试确认Python、QtCore、QtWidgets正常。
## 修复
在Jetson本机桌面Ctrl+Alt+T启动终端，获得wayland、DISPLAY=:0、WAYLAND_DISPLAY=wayland-0；15秒自动关闭测试窗口成功。
## 判断
SSH可装包但不自动拥有显示会话；不盲设DISPLAY绕过桌面授权。GUI事件循环不返回提示符是正常运行。
## 边界
最初“无输出”的完整根因未确定，heredoc未结束是排查分支而非确认原因。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

