#!/usr/bin/env python3
"""检查Qt环境；--test-window只在已有图形会话打开15秒窗口。"""
import argparse
import os
import sys

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--test-window", action="store_true")
    a = p.parse_args()
    print("Python:", sys.executable, flush=True)
    for key in ("XDG_SESSION_TYPE", "DISPLAY", "WAYLAND_DISPLAY"):
        print(key, "=", os.getenv(key), flush=True)
    if a.test_window and not (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
        p.error("请从已登录的Jetson图形桌面终端运行，不盲设DISPLAY")
    from PySide6 import QtCore, QtWidgets
    print("PySide6:", QtCore.__version__, flush=True)
    if a.test_window:
        app = QtWidgets.QApplication(sys.argv[:1])
        w = QtWidgets.QLabel("Jetson YOLO GUI · Qt窗口成功")
        w.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        w.resize(600, 240); w.show()
        QtCore.QTimer.singleShot(15000, app.quit)
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
