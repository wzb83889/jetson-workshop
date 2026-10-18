# Jetson 创新工坊 · Jetson Workshop

把真实的 Jetson 探索沉淀为可复现的脚本、故障案例和边缘 AI 示例。维护者：Brad（GitHub: wzb83889）。

## 当前成果

- Orin Nano 8GB：CUDA 与容器真实运算、PyTorch GPU 算子与数值校验。
- YOLOv8n：PyTorch GPU → ONNX → TensorRT FP16。
- 同一图片640×640，预热10次后测试50次：推理21.33 → 5.74ms（约3.72倍），三个处理阶段33.10 → 20.34ms（约1.63倍）。
- PySide6 图片与本地视频检测界面。
- llama.cpp CUDA、Qwen本地问答、回环API和SSH隧道。

**历史GPU与GUI主路径已在Jetson验证；新增参数与重构需在目标Jetson复验，维护工具也待实机验收。** GUI示例为按已有记录重建的整理版，尚未收回Jetson上的两份实际成功源码。本次归档环境没有Jetson GPU，不冒充硬件复验。

## 先看哪里

1. [环境基准](docs/baseline.md) 与 [安装组合](docs/yolo-environment.md)。
2. [GPU验证](docs/gpu-validation.md) → [TensorRT导出](docs/tensorrt-export.md) → [实测结果](docs/benchmark-2026-10-17.md)。
3. [图片GUI](docs/gui.md)、[视频GUI](docs/video-gui.md)与[桌面入口](docs/desktop-launcher.md)。
4. [路线图](ROADMAP.md)、[贡献说明](CONTRIBUTING.md)、[归档流程](docs/knowledge-workflow.md)。
5. [系统常规维护](docs/routine-maintenance.md)：原维护工具包的检查、计划与验证入口。

## 工具索引

| 位置 | 内容 |
| --- | --- |
| scripts/inspect_jetson.sh | 环境快照 |
| scripts/cuda_smoke.cu、gpu_smoke.py | CUDA向量与PyTorch算子数值验证 |
| scripts/export_yolo.py、benchmark_yolo.py | TensorRT导出和统一条件测速 |
| scripts/download_samples.py | 官方示例下载与校验 |
| scripts/desktop_session_check.py、install_desktop_launcher.py | 图形会话检查与桌面双击入口 |
| scripts/restore_nvidia_shortcuts.py | 恢复缺失NVIDIA快捷方式 |
| scripts/start_llm.sh、new_session.py | 本地LLM启动与独立复盘模板 |
| examples/yolo_gui.py、yolo_video_gui.py | 图片与视频GUI整理版 |
| maintenance/ | 原维护工具与离线模拟测试 |

## 可运行入口

在已有验证环境中：
```bash
~/venvs/yolo/bin/python scripts/gpu_smoke.py
~/venvs/yolo/bin/python scripts/benchmark_yolo.py --pt ~/jetson-lab/yolo/yolov8n.pt --engine ~/jetson-lab/yolo/yolov8n.engine --image ~/jetson-lab/yolo/bus.jpg
~/venvs/yolo/bin/python examples/yolo_video_gui.py
```

GUI默认查找 ~/jetson-lab/yolo/ 下模型，可通过 JETSON_YOLO_WORKDIR 指定另一目录。先选择模型和素材，程序不会主动安装依赖。

## 兼容边界

历史组合：JetPack7.2.1 / L4T39.2.1 / CUDA13.2 / TensorRT10.16.2.10 / Python3.12 / torch2.12.0+cu132 / Ultralytics8.4.179。不是所有Jetson系统的通用安装保证。CC8.7警告保留；已测算子可用不代表所有扩展可用。模型、视频、引擎及原始日志不随仓库分发。

原作者代码采用MIT；Ultralytics等依赖与素材仍适用其各自许可，参见[第三方说明](THIRD_PARTY.md)。不将原始私人台账或设备凭据发布到仓库。

## 存储与桌面响应

[microSD 卡顿诊断与 NVMe 全系统迁移](docs/storage-migration.md)：先采样定位，再进行同版、一致性、可回退迁移。当前为待实机验证的方案。
