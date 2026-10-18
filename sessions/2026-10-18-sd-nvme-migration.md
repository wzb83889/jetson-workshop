# 2026-10-18 · microSD 卡顿调查与 NVMe 迁移规划

session_id: 2026-10-18-sd-nvme-migration
状态: 计划，未实机诊断，未迁移

## 目标与证据

对已使用 microSD 的 Orin Nano 系统出现的高频菜单停顿进行分层诊断，并规划保留既有环境的 NVMe 迁移。已有台账证明历史根盘是 microSD，最近 swap 为 0；本轮只有现象反馈，尚无卡顿时 I/O、内存、日志或 GUI 线程证据。

## 判断边界

SD 随机读写等待是候选原因；还需排查共享内存压力、单个 GUI 同步推理、CPU/温度/桌面异常。不能据症状判卡损坏，不能保证 SSD 消除所有 UI 停顿。

## 本次变更

- 新增 docs/storage-migration.md，给出只读采样、两种同版迁移路线、完整环境范围、独立启动验收与回退。
- 同步 README、CHANGELOG 和 ROADMAP。
- 没有新增或执行磁盘迁移脚本；没有修改目标 Jetson、固件或 SD。

## 验证

已核对 NVIDIA JetPack 7.2.1 的 ISO 安装、NVMe 接口与 R39.2.1 引导/克隆文档。已静态审阅方案与去敏内容；本轮无硬件测试或性能提升结果，文档变更无需新增镜像实现的测试。

## 接续与完成标准

先收回实际卡顿采样和当前磁盘/引导布局，再确定 SSD 与一致性维护环境。迁移完成必须在关机取出 SD 后从 NVMe 启动，根与 EFI 无旧卡依赖，原 CUDA/YOLO/LLM/实际容器通过，并复测同一菜单负载。原 SD 保留回退；完整方法见 docs/storage-migration.md。
