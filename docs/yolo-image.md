# YOLOv8n：GPU 图片检测

编号：JKB-006 · 历史验证：已实测 · 最近整理：2026-10-18

## 已验证
日志明确CUDA:0 (Orin)。bus.jpg用640×480矩形输入识别4人、1公交车、1停车标志；改成固定640×640后与TensorRT均4人1公交车。
## 运行
```bash
yolo predict model=yolov8n.pt source=bus.jpg device=0 imgsz=640 save=True show=False
```
## 排障
权重下载SSL EOF重试后成功，不是CUDA故障。
## 边界
通用COCO模型没有安全帽/反光衣类别；对指定人的姓名/身份识别也不属于这个目标检测任务。

来源：个人Jetson实测记录；仓库脚本整理版需要目标设备复验。

