# 桌面双击启动：.desktop 与日志

编号：JKB-012 · 历史验证：待验收 · 最近整理：2026-10-18

## 方案
.desktop调用用户级shell脚本，再用venv绝对Python启动GUI；Terminal=false；日志进入用户.local/state。
## 已有内容
上一轮已提供创建脚本，未获得执行与双击成功反馈。首次可能需右键“允许启动”。
## 整理版
scripts/install_desktop_launcher.py 支持--dry-run，显式目标、桌面目录与日志；需要在用户图形环境实际验收。
## 边界
这不是开机自启、系统服务、跨设备独立安装包，也不会替用户激活远程图形会话。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

