#!/usr/bin/env python3
"""安装当前用户YOLO桌面入口；默认不覆盖已有文件，支持--dry-run。"""
import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

def desktop_entry(launcher):
    escaped=str(launcher).replace("\\","\\\\").replace('"','\\"').replace("$","\\$").replace("`","\\`").replace("%","%%")
    return ("[Desktop Entry]\nType=Application\nName=Jetson YOLO 检测\n"
            "Comment=图片与视频目标检测\n"
            f'Exec="{escaped}"\nIcon=camera-video\nTerminal=false\n'
            "Categories=Graphics;Education;\nStartupNotify=false\n")

def launch_script(python, program, log):
    q=shlex.quote
    return ("#!/bin/sh\n"
      f"cd {q(str(program.parent))} || exit 1\n"
      "export YOLO_AUTOINSTALL=False\n"
      f"{q(str(python))} -u {q(str(program))} >> {q(str(log))} 2>&1\n"
      "code=$?\n"
      'if [ "$code" -ne 0 ] && command -v zenity >/dev/null 2>&1; then\n'
      f"  zenity --error --text={q('YOLO启动失败，日志：'+str(log))}\n"
      "fi\n"
      'exit "$code"\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--python",type=Path,default=Path(sys.executable))
    p.add_argument("--program",type=Path,
       default=Path(__file__).resolve().parents[1]/"examples/yolo_video_gui.py")
    p.add_argument("--home",type=Path,default=Path.home(),
       help="明确的目标用户主目录；默认当前用户")
    p.add_argument("--desktop",type=Path)
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--force",action="store_true",help="允许覆盖已有入口")
    a=p.parse_args()
    # 不resolve解释器symlink，否则可能丢失venv入口。
    python=a.python.expanduser().absolute()
    program=a.program.expanduser().resolve()
    home=a.home.expanduser().resolve()
    if not python.is_file() or not os.access(python,os.X_OK) or not program.is_file():
        p.error("解释器不可执行或程序不存在")
    if a.desktop:
        desktop=a.desktop.expanduser().absolute()
    elif home==Path.home():
        try:
            desktop=Path(subprocess.check_output(["xdg-user-dir","DESKTOP"],text=True).strip())
        except (OSError,subprocess.CalledProcessError):
            desktop=home/"Desktop"
    else:
        desktop=home/"Desktop"
    launcher=home/".local/bin/jetson-yolo-gui"
    app=home/".local/share/applications/jetson-yolo-gui.desktop"
    shortcut=desktop/app.name
    log=home/".local/state/jetson-yolo-gui/launch.log"
    outputs={launcher:launch_script(python,program,log),
             app:desktop_entry(launcher),shortcut:desktop_entry(launcher)}
    print(json.dumps({"files":[str(x) for x in outputs],
                     "log":str(log),"dry_run":a.dry_run},ensure_ascii=False,indent=2))
    if a.dry_run:
        return
    existing=[str(x) for x in outputs if x.exists()]
    if existing and not a.force:
        p.error("入口已存在；先检查或备份，确认覆盖时加--force："+", ".join(existing))
    log.parent.mkdir(parents=True,exist_ok=True)
    for path,body in outputs.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("w" if a.force else "x",encoding="utf-8") as f:
            f.write(body)
        path.chmod(0o755)
    if shutil.which("gio") and (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
        subprocess.run(["gio","set",str(shortcut),"metadata::trusted","true"],check=False)
    print("已创建；必要时在桌面右键允许启动。此操作不配置开机自启。")

if __name__=="__main__":
    main()
