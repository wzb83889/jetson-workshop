# llama.cpp CUDA：Qwen 本地模型与 API

编号：JKB-013 · 历史验证：已实测 · 最近整理：2026-10-18

## 历史已完成
llama.cpp b1-d81aef1，GGML_CUDA=ON、CMAKE_CUDA_ARCHITECTURES=87、单并行构建。Qwen3-1.7B Q8与Qwen3.5-4B Q4_K_M文本首测通过。
## 服务
回环地址127.0.0.1:8080、-ngl99、-c2048、-np1、--no-ui。tmux会话分离后健康检查成功。
## 实际负载
1.7B生成期间tegrastats GR3D_FREQ90%～99%，空闲降回0%。
## 模型差异
Qwen3.5-4B用--reasoning off获得正确短答，不机械套用旧Qwen3/no_think；未加载mmproj，视觉能力未测试。
## 边界
短回答token/s不用于长期性能排名；4B详细逐层卸载和长文本峰值仍待证据。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

