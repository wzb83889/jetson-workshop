# 2026-10-17～18 · YOLO TensorRT 与 GUI

session_id: 2026-10-17-yolo-tensorrt
验证: partial

## 已实测
PyTorch2.12.0+cu132与GPU数值算子；YOLOv8n图片GPU推理；ONNX→TRT FP16；引擎加载和50轮统一条件比较；图片GUI；视频GUI连续检测。

## 性能
同图640×640，batch1，预热10、测50。PT FP32推理21.33ms、TRT FP16 5.74ms，3.72倍。三阶段33.10→20.34ms，1.63倍。不是整机摄像头FPS；未同步记录频率/温度/电源模式。

## 故障与判断
ensurepip缺失→模拟后补python3.12-venv；缺onnx→补依赖并关闭可选简化；TTY无DISPLAY→在Wayland桌面启动；CC8.7警告→算子和模型逐层验证，保留警告。

## 待验收
停止/保存/重启、桌面启动器、新工地视频、PPE模型及摄像头。
仓库整理版参数与重构尚需独立硬件验收。

## 同步
Notion主题编号JKB-001～017。私人台账不原样发布。
