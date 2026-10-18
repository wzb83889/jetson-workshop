#!/usr/bin/env python3
"""本机导出静态640 TensorRT FP16，禁止自动安装依赖。"""
import argparse
import os
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("model", type=Path)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--workspace", type=float, default=1.0)
    a = p.parse_args()
    if not a.model.is_file() or a.model.suffix != ".pt":
        p.error("需要本地.pt权重")
    if a.imgsz <= 0 or a.imgsz % 32 or a.workspace <= 0:
        p.error("imgsz须为正32倍数，workspace须大于0")
    target = a.model.with_suffix(".engine")
    if target.exists():
        p.error("目标engine已存在，请先备份或更换模型文件名")
    os.environ["YOLO_AUTOINSTALL"] = "False"
    from ultralytics import YOLO
    result = YOLO(str(a.model), task="detect").export(
        format="engine", device=0, imgsz=a.imgsz, batch=1, dynamic=False,
        quantize=16, workspace=a.workspace, simplify=False, opset=17)
    print("导出完成：", result)
    print("请继续加载引擎推理验收；工作区限制不是总内存限制。")

if __name__ == "__main__":
    main()
