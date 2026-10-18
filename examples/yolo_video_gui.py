#!/usr/bin/env python3
"""本地视频GUI；视频内复用模型。仓库整理版待目标设备复验。"""
import sys
import time
import threading
from collections import Counter
from yolo_gui import Window, ROOT, cv2, QtCore, QtWidgets

class VideoDetector(QtCore.QThread):
    frame=QtCore.Signal(object,object,str,int,int)
    error=QtCore.Signal(str)
    status=QtCore.Signal(str)
    def __init__(self,model_path,video_path,conf,iou):
        super().__init__()
        self.model_path=model_path; self.video_path=video_path
        self.conf=conf; self.iou=iou; self.stop_event=threading.Event()
    def stop(self):
        self.stop_event.set()
    def run(self):
        cap=None
        try:
            from ultralytics import YOLO
            self.status.emit("正在加载模型…")
            model=YOLO(self.model_path,task="detect")
            if self.stop_event.is_set():
                return
            cap=cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                raise RuntimeError("视频无法打开，请检查文件/编码")
            total=max(0,int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            fps=cap.get(cv2.CAP_PROP_FPS)
            interval=1.0/fps if 0<fps<1000 else 0
            index=0
            while not self.stop_event.is_set():
                started=time.perf_counter()
                ok,image=cap.read()
                if not ok:
                    if not index:
                        raise RuntimeError("无法解码第一帧")
                    self.status.emit("视频读取结束（EOF或解码中断），保留最后一帧")
                    break
                r=model.predict(source=image,device=0,imgsz=640,rect=False,conf=self.conf,
                                iou=self.iou,save=False,verbose=False)[0]
                annotated=r.plot()
                counts=Counter(r.names[int(c)] for c in r.boxes.cls.cpu().tolist())
                summary="\n".join(f"{n}: {v}" for n,v in counts.items()) or "当前帧未检测到目标"
                index+=1
                elapsed=(time.perf_counter()-started)*1000
                summary+=(f"\n\n推理：{r.speed['inference']:.2f} ms"
                          f"\n本帧读取/处理/画框：{elapsed:.2f} ms"
                          "\n\n数量为当前帧，非累计人次。")
                self.frame.emit(image,annotated,summary,index,total)
                remaining=interval-(time.perf_counter()-started)
                if remaining>0:
                    self.stop_event.wait(remaining)
            if self.stop_event.is_set():
                self.status.emit("已停止，保留最后一帧")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"{type(e).__name__}: {e}")
        finally:
            if cap is not None:
                cap.release()

class VideoWindow(Window):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jetson YOLO GUI · 图片/视频 · GPU/TensorRT")
        self.video_path=None
        self.open_video_button=QtWidgets.QPushButton("打开本地视频")
        self.open_video_button.clicked.connect(self.open_video)
        self.stop_button=QtWidgets.QPushButton("停止视频")
        self.stop_button.setEnabled(False); self.stop_button.clicked.connect(self.stop_video)
        self.progress=QtWidgets.QProgressBar(); self.progress.setRange(0,100); self.progress.setValue(0)
        sidebar=self.layout().itemAt(0).widget().layout()
        for pos,w in enumerate((self.open_video_button,self.stop_button,self.progress),1):
            sidebar.insertWidget(pos,w)
    def open_image(self):
        previous=self.image; super().open_image()
        if self.image is not previous:
            self.video_path=None; self.run_button.setText("开始检测")
            self.progress.setRange(0,100); self.progress.setValue(0)
    def open_video(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,"选择本地视频",str(ROOT),
                           "视频 (*.mp4 *.avi *.mkv *.mov *.webm *.m4v);;所有文件 (*)")
        if not path:
            return
        cap=cv2.VideoCapture(path)
        ok,image=cap.read(); cap.release()
        if not ok:
            QtWidgets.QMessageBox.warning(self,"读取失败","无法读取视频第一帧"); return
        self.video_path=path; self.image=image; self.output=None
        self.original.set_image(image); self.detected.picture=None
        self.detected.clear(); self.detected.setText("等待视频检测")
        self.results.setPlainText("点击开始视频检测"); self.save_button.setEnabled(False)
        self.run_button.setText("开始视频检测")
        self.progress.setRange(0,100); self.progress.setValue(0); self.status.setText("视频就绪")
    def detect(self):
        if self.video_path is None:
            super().detect(); return
        if not self.model.currentData():
            QtWidgets.QMessageBox.information(self,"提示","请先选择模型"); return
        self.set_busy(True); self.output=None; self.stop_button.setEnabled(True)
        self.status.setText("准备视频检测…")
        self.worker=VideoDetector(self.model.currentData(),self.video_path,self.conf.value(),self.iou.value())
        self.worker.frame.connect(self.show_video_frame,QtCore.Qt.ConnectionType.BlockingQueuedConnection)
        self.worker.error.connect(self.show_error); self.worker.status.connect(self.status.setText)
        self.worker.finished.connect(self.finished); self.worker.start()
    @QtCore.Slot(object,object,str,int,int)
    def show_video_frame(self,original,annotated,summary,index,total):
        self.original.set_image(original); self.detected.set_image(annotated)
        self.output=annotated; self.results.setPlainText(summary)
        if total>0:
            self.progress.setRange(0,total); self.progress.setValue(min(index,total))
            self.progress.setFormat(f"第 {index} / {total} 帧")
        else:
            self.progress.setRange(0,0)
        self.status.setText("视频检测中 · 处理较慢时播放会变慢")
    def set_busy(self,busy):
        super().set_busy(busy)
        if hasattr(self,"open_video_button"):
            self.open_video_button.setEnabled(not busy)
        if hasattr(self,"stop_button") and not busy:
            self.stop_button.setEnabled(False)
    def stop_video(self):
        if isinstance(self.worker,VideoDetector) and self.worker.isRunning():
            self.worker.stop(); self.stop_button.setEnabled(False)
            self.status.setText("正在停止，等待当前加载或当前帧完成…")
    def finished(self):
        super().finished(); self.stop_button.setEnabled(False)
        if self.progress.maximum()==0:
            self.progress.setRange(0,100); self.progress.setValue(0)
    def closeEvent(self,event):
        if isinstance(self.worker,VideoDetector) and self.worker.isRunning():
            self.stop_video(); event.ignore()
        else:
            super().closeEvent(event)

if __name__=="__main__":
    import os
    if not(os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
        sys.exit("请在Jetson图形桌面启动。")
    app=QtWidgets.QApplication(sys.argv)
    window=VideoWindow(); window.show(); sys.exit(app.exec())
