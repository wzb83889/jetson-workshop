# GPU 验收：从可导入到实际数值运算

编号：JKB-003 · 历史验证：已实测 · 最近整理：2026-10-18

## 验收顺序
解释器与版本 → CUDA可见 → 数值矩阵运算 → GPU NMS → FP32/FP16卷积、SiLU、缩放 → YOLO整模型。
## 实测
torch 2.12.0+cu132、torchvision 0.27.0+cu132；CUDA可用。256×256全1矩阵乘法预期256；重叠框NMS预期[0]，均通过。
## 警告
get_arch_list未列sm_87，初始化出现except {8.7}警告。本次已测路径能运行；尚未证明所有算子、Triton或torch.compile路径可用，也不推断底层回退机制。
## 代码
scripts/gpu_smoke.py 为整理版，需要在Jetson重新验收。
## 边界
is_available=True不是完整验收，nvidia-smi的N/A也不能单独判失败。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

