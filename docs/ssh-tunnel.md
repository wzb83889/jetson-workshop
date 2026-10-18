# SSH 隧道：Windows 18080 保留端口问题

编号：JKB-014 · 历史验证：已实测 · 最近整理：2026-10-18

## 现象
本机18080绑定Permission denied；Windows excludedportrange中18034～18133包含18080。
## 有效方案
改用18888，本地转发到Jetson回环8080：
```bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18888:127.0.0.1:8080 USER@JETSON_IP
```
## 判断
本机端口排除不靠修改Jetson防火墙解决。SSH Connection refused先查22监听；API拒绝先查模型服务和8080监听。
## 边界
关闭隧道不等于停止tmux中的模型服务；仍占内存。未开公网端口。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

