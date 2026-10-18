# 常规维护：检查、计划与显式升级

编号：JKB-018 · 状态：历史维护记录部分验证；工具待Jetson验收。

## 来源与代码

`maintenance/`中的三个Python文件逐字取自先前交付的Jetson-Maintenance-v1.0工具包；没有在本次归档时改写安装逻辑。原工具包SHA256：`71cdc2650eda3597a3652a02f8d916d99279b5e98f825f44e2bd65f180f1913f`。原维护手册含私人现场细节，不公开；此页为整理说明。

- [jetson-maint.py](../maintenance/jetson-maint.py)：标准库工具，包含check / plan / apply / verify。
- [gpu-smoke.py](../maintenance/gpu-smoke.py)：分别检查torch矩阵运算或TRT构建/反序列化。TRT模式**没有执行推理**。
- [test-maintenance.py](../maintenance/test-maintenance.py)：5项离线模拟测试，不执行APT或改变服务。

## 从检查开始

```bash
sudo python3 maintenance/jetson-maint.py check
sudo python3 maintenance/jetson-maint.py plan
~/venvs/yolo/bin/python maintenance/gpu-smoke.py torch
~/venvs/yolo/bin/python maintenance/gpu-smoke.py tensorrt
```

check读取系统并保存本地日志；plan会刷新APT索引和模拟升级，不安装软件包。日志在`/var/log/jetson-maint/`，包含机器信息，**不要直接提交日志**。先人工检查当前状态和候选事务，再决定是否显式选择普通包。apply要求明确包名、事务检查与交互确认；没有无人值守升级或自动回滚承诺。

关键平台包、内核、启动、网络或底层库需要独立维护方案；不要把此工具当作通用JetPack升级器。工具的配置备份不是可启动镜像。升级后verify仍不等于GPU与业务验收，需另跑实际模型任务。

## 可复用案例

- ARM64二进制索引应核对实际源与suite；部分APT索引失败可能继续使用旧缓存。本工具使用严格错误模式。
- 失败的独立DHCP/dnsmasq实例，可能与NVIDIA USB设备模式实例不同。先看PID、unit、配置和监听，不按名称批量停服务。
- NetworkManager、systemd-resolved和NVIDIA USB关键服务的当次检查已有历史通过记录；服务处置后跨重启与本轮GPU业务复核仍待证据。

## 本次验证

本次读取原文件、检查Python语法并运行5项模拟测试通过；未在Jetson执行维护、APT安装或GPU测试。
