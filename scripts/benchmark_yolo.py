#!/usr/bin/env python3
"""PT FP32与已构建TRT引擎比较；输出阶段耗时，不冒充摄像头FPS。"""
import argparse
import gc
import json
import os
import statistics
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("pt", "engine", "image"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--repeat", type=int, default=50)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if a.repeat < 1 or a.warmup < 0 or a.imgsz < 32 or a.imgsz % 32:
        p.error("轮数或imgsz无效")
    if any(not f.is_file() for f in (a.pt, a.engine, a.image)):
        p.error("模型/图片文件不存在")
    if a.output and a.output.exists():
        p.error("输出文件已存在，请换名")
    os.environ["YOLO_AUTOINSTALL"] = "False"
    import cv2
    import torch
    import ultralytics
    from ultralytics import YOLO
    image = cv2.imread(str(a.image))
    if image is None:
        p.error("图片不可解码")
    report = {"torch": torch.__version__, "ultralytics": ultralytics.__version__,
        "cuda": torch.version.cuda, "imgsz": a.imgsz, "batch": 1,
        "warmup": a.warmup, "repeat": a.repeat, "power_mode": "未自动采集",
        "scope": "PT FP32 vs TRT构建精度；仅三个处理阶段，非端到端视频FPS", "models": []}
    for path in (a.pt, a.engine):
        model = YOLO(str(path), task="detect")
        args = dict(source=image, device=0, imgsz=a.imgsz, rect=False,
                    conf=0.25, iou=0.7, half=False, save=False, verbose=False)
        for _ in range(a.warmup):
            model.predict(**args)
        times = []
        for _ in range(a.repeat):
            result = model.predict(**args)[0]
            times.append(result.speed.copy())
        entry = {"model": path.name, "stage_ms": {}, "last_detection": result.verbose()}
        for stage in ("preprocess", "inference", "postprocess"):
            values = [t[stage] for t in times]
            entry["stage_ms"][stage] = {"mean": statistics.mean(values),
                "median": statistics.median(values)}
        entry["three_stage_mean_ms"] = statistics.mean(
            sum(t[k] for k in ("preprocess","inference","postprocess")) for t in times)
        report["models"].append(entry)
        del result, model
        gc.collect()
        torch.cuda.empty_cache()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with a.output.open("x", encoding="utf-8") as f:
            f.write(text + "\n")

if __name__ == "__main__":
    main()
