# 容器 CDI：enable-cuda-compat Hook 越界

编号：JKB-004 · 历史验证：已实测 · 最近整理：2026-10-18

## 现象
镜像拉取成功但OCI创建失败，Go堆栈指向nvidia-cdi-hook/cudacompat，slice bounds out of range。
## 已排除
Docker服务、nvidia runtime注册和1.19.1组件版本一致。
## 有效修复
生成临时CDI清单禁用enable-cuda-compat先测试；持久配置通过nvidia-cdi-refresh.env的NVIDIA_CTK_CDI_GENERATE_DISABLED_HOOKS=enable-cuda-compat，运行模式固定cdi。
## 核心区别
runtime功能开关、清单生成参数、实际runtime模式是不同控制层。单改disable-cuda-compat-lib-hook未修复本机已生成的CDI清单。
## 验收
容器内1,048,576元素CUDA向量加法与逐项校验PASS。
## 边界
跨重启CDI持续性和后续Toolkit升级后的上游修复未在此资料中完成验收。使用版本相关修复前先检查本机配置并备份。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

