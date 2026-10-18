#!/usr/bin/env python3
"""从/etc/skel/Desktop恢复NVIDIA快捷方式；独占创建、不覆盖已有文件。"""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

NAMES = ("nv_devzone", "nv_forums", "nv_jetson_projects", "nv_jetson_zoo")
def restore(source, target):
    target = Path(target); source = Path(source)
    if target.exists():
        return "已存在，保留"
    if not source.is_file():
        return "源文件缺失"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        target.chmod(source.stat().st_mode & 0o777)
    except FileExistsError:
        return "已存在，保留"
    return "已恢复"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desktop",type=Path)
    p.add_argument("--dry-run",action="store_true")
    a=p.parse_args()
    if a.desktop:
        desktop=a.desktop.expanduser()
    else:
        try:
            desktop=Path(subprocess.check_output(["xdg-user-dir","DESKTOP"],text=True).strip())
        except (OSError,subprocess.CalledProcessError):
            desktop=Path.home()/"Desktop"
    for n in NAMES:
        src=Path("/etc/skel/Desktop")/(n+".desktop"); dst=desktop/src.name
        print(src.name, "预览："+str(dst) if a.dry_run else restore(src,dst))

if __name__=="__main__":
    main()
