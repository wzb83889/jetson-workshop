#!/usr/bin/env python3
"""只下载来源明确的Intel示例；检查MP4文件头，原子替换临时文件。"""
import argparse
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path

SAMPLES = {
 "traffic": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4",
 "worker-zone": "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/worker-zone-detection.mp4",
}
def download(url, target, opener=urllib.request.urlopen):
    target = Path(target)
    if target.exists():
        raise FileExistsError("目标已存在，不覆盖：" + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=target.name + ".", suffix=".part", dir=target.parent)
    digest = hashlib.sha256()
    try:
        with os.fdopen(fd, "wb") as out:
            with opener(url, timeout=30) as response:
                header = response.read(64)
                if len(header) < 12 or header[4:8] != b"ftyp":
                    raise ValueError("内容不是预期MP4文件，拒绝保存")
                out.write(header); digest.update(header)
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    out.write(block); digest.update(block)
        # 独占创建目标，避免并发覆盖。
        os.link(temp, target)
        os.unlink(temp)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return digest.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sample", choices=SAMPLES)
    p.add_argument("--directory", type=Path, default=Path.home()/"jetson-lab/yolo/videos")
    a = p.parse_args()
    target = a.directory/(a.sample+".mp4")
    print("来源：Intel sample-videos，CC BY 4.0；不是现场精度数据集。")
    print("路径：", target)
    print("SHA256:", download(SAMPLES[a.sample], target))
    print("文件头通过；请继续在GUI验收解码与内容。")

if __name__ == "__main__":
    main()
