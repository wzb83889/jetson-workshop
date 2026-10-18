# ONNX → TensorRT FP16 最小导出链

编号：JKB-007 · 历史验证：已实测 · 最近整理：2026-10-18

## 有效命令
```bash
YOLO_AUTOINSTALL=False yolo export model=yolov8n.pt format=engine device=0 imgsz=640 batch=1 dynamic=False quantize=16 workspace=1 simplify=False opset=17
```
## 结果
ONNX1.19.1导出2.6s/12.2MB；TRT10.16.2.10导出497.1s/8.3MB；输入1×3×640×640，输出1×84×8400。
## 排障
缺onnx时尚未进入TRT构建。simplify=False跳过可选onnxslim/ONNX Runtime简化链。workspace=1不是总内存上限。I/O FLOAT不否认内部FP16。
## 复用
引擎成功后要实际加载推理；引擎与硬件/运行时相关，升级栈后复验，不将别人的engine视作本机已适配。
## 边界
构建耗时不是每帧耗时；本次参数适用于已验证的Ultralytics版本。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

