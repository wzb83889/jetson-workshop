#!/usr/bin/env python3
"""图片GUI。历史原型已实测；仓库整理版需Jetson复验。"""
import os
import sys
from pathlib import Path
from collections import Counter
os.environ["YOLO_AUTOINSTALL"]="False"
import cv2
from PySide6 import QtCore, QtGui, QtWidgets

for key in ("QT_QPA_PLATFORM_PLUGIN_PATH","QT_QPA_FONTDIR"):
    if "cv2" in os.environ.get(key,""):
        os.environ.pop(key)
ROOT=Path(os.environ.get("JETSON_YOLO_WORKDIR",str(Path.home()/"jetson-lab/yolo"))).expanduser()

class Detector(QtCore.QThread):
    result=QtCore.Signal(object,str)
    error=QtCore.Signal(str)
    def __init__(self,model_path,image,conf,iou):
        super().__init__()
        self.model_path=model_path; self.image=image.copy()
        self.conf=conf; self.iou=iou
    def run(self):
        try:
            from ultralytics import YOLO
            model=YOLO(self.model_path,task="detect")
            r=model.predict(source=self.image,device=0,imgsz=640,rect=False,
                 conf=self.conf,iou=self.iou,save=False,verbose=False)[0]
            counts=Counter(r.names[int(c)] for c in r.boxes.cls.cpu().tolist())
            summary="\n".join(f"{n}: {v}" for n,v in counts.items()) or "未检测到目标"
            summary+="\n\n本次耗时（含首次运行影响）\n"
            labels={"preprocess":"预处理","inference":"推理","postprocess":"后处理"}
            summary+="\n".join(f"{labels.get(k,k)}: {v:.2f} ms" for k,v in r.speed.items())
            self.result.emit(r.plot(),summary)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(f"{type(e).__name__}: {e}")

class ImageView(QtWidgets.QLabel):
    def __init__(self,text):
        super().__init__(text)
        self.picture=None
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(240,240)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background:#17202d;color:#cbd5e1;border:1px solid #475569;border-radius:6px;")
    def set_image(self,bgr):
        rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
        h,w,_=rgb.shape
        image=QtGui.QImage(rgb.data,w,h,rgb.strides[0],
                          QtGui.QImage.Format.Format_RGB888).copy()
        self.picture=QtGui.QPixmap.fromImage(image)
        self.refresh()
    def refresh(self):
        if self.picture is not None:
            self.setPixmap(self.picture.scaled(self.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation))
    def resizeEvent(self,event):
        super().resizeEvent(event); self.refresh()

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.image=None; self.output=None; self.worker=None
        self.setWindowTitle("Jetson YOLO GUI · GPU / TensorRT")
        self.resize(1180,680)
        self.model=QtWidgets.QComboBox()
        for name in ("yolov8n.engine","yolov8n.pt"):
            path=ROOT/name
            if path.is_file():
                self.model.addItem(name,str(path))
        self.choose_model=QtWidgets.QPushButton("选择其他模型")
        self.choose_model.clicked.connect(self.open_model)
        self.open_button=QtWidgets.QPushButton("打开图片")
        self.open_button.clicked.connect(self.open_image)
        self.run_button=QtWidgets.QPushButton("开始检测")
        self.run_button.clicked.connect(self.detect)
        self.save_button=QtWidgets.QPushButton("保存检测图片")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        self.conf=QtWidgets.QDoubleSpinBox(); self.iou=QtWidgets.QDoubleSpinBox()
        for spin,value in ((self.conf,0.25),(self.iou,0.70)):
            spin.setRange(0.01,1.0); spin.setSingleStep(0.05); spin.setValue(value)
        form=QtWidgets.QFormLayout()
        form.addRow("模型",self.model); form.addRow(self.choose_model)
        form.addRow("置信度",self.conf); form.addRow("IoU 去重阈值",self.iou)
        for widget in (self.open_button,self.run_button,self.save_button):
            form.addRow(widget)
        self.results=QtWidgets.QPlainTextEdit(); self.results.setReadOnly(True)
        self.results.setPlainText("先打开图片，再开始检测。")
        sidebar=QtWidgets.QVBoxLayout(); sidebar.addLayout(form)
        sidebar.addWidget(QtWidgets.QLabel("识别结果")); sidebar.addWidget(self.results)
        panel=QtWidgets.QWidget(); panel.setLayout(sidebar); panel.setFixedWidth(260)
        self.original=ImageView("原始图片"); self.detected=ImageView("检测结果")
        previews=QtWidgets.QHBoxLayout()
        for title,view in (("原始图片",self.original),("检测结果",self.detected)):
            column=QtWidgets.QVBoxLayout(); column.addWidget(QtWidgets.QLabel(title))
            column.addWidget(view); previews.addLayout(column,1)
        self.status=QtWidgets.QLabel("就绪 · 输入640×640 · GPU 0")
        content=QtWidgets.QVBoxLayout(); content.addLayout(previews,1); content.addWidget(self.status)
        layout=QtWidgets.QHBoxLayout(self); layout.addWidget(panel); layout.addLayout(content,1)
    def open_model(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,"选择检测模型",str(ROOT),
                                                    "YOLO检测模型 (*.pt *.engine)")
        if path:
            self.model.addItem(Path(path).name,path)
            self.model.setCurrentIndex(self.model.count()-1)
    def open_image(self):
        path,_=QtWidgets.QFileDialog.getOpenFileName(self,"打开图片",str(ROOT),
                                                    "图片 (*.jpg *.jpeg *.png *.bmp *.webp)")
        if not path:
            return
        image=cv2.imread(path)
        if image is None:
            QtWidgets.QMessageBox.warning(self,"读取失败","无法读取此图片"); return
        self.image=image; self.output=None
        self.original.set_image(image); self.detected.picture=None
        self.detected.clear(); self.detected.setText("等待检测")
        self.save_button.setEnabled(False); self.results.clear()
        self.status.setText("已打开："+Path(path).name)
    def detect(self):
        if self.image is None or not self.model.currentData():
            QtWidgets.QMessageBox.information(self,"提示","请先选择模型并打开图片"); return
        self.set_busy(True); self.output=None
        self.status.setText("加载模型并检测，首次运行可能稍慢…")
        self.worker=Detector(self.model.currentData(),self.image,self.conf.value(),self.iou.value())
        self.worker.result.connect(self.show_result); self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.finished); self.worker.start()
    def set_busy(self,busy):
        for w in (self.model,self.choose_model,self.open_button,self.run_button,self.conf,self.iou):
            w.setEnabled(not busy)
        self.save_button.setEnabled(not busy and self.output is not None)
    @QtCore.Slot(object,str)
    def show_result(self,image,summary):
        self.output=image; self.detected.set_image(image)
        self.results.setPlainText(summary); self.status.setText("检测完成")
    def show_error(self,message):
        self.status.setText("检测失败，详见终端/启动日志")
        QtWidgets.QMessageBox.critical(self,"检测失败",message)
    def finished(self):
        self.set_busy(False)
    def save_image(self):
        if self.output is None:
            return
        path,_=QtWidgets.QFileDialog.getSaveFileName(self,"保存检测图片",str(ROOT/"gui_result.png"),"PNG (*.png)")
        if not path:
            return
        if not Path(path).suffix:
            path+=".png"
        try:
            ok=cv2.imwrite(path,self.output)
        except cv2.error:
            ok=False
        if ok:
            self.status.setText("已保存："+path)
        else:
            QtWidgets.QMessageBox.warning(self,"保存失败","无法写入文件")
    def closeEvent(self,event):
        if self.worker is not None and self.worker.isRunning():
            self.status.setText("检测正在执行，请完成后再关闭"); event.ignore()
        else:
            event.accept()

def main():
    if not (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
        raise SystemExit("请在Jetson图形桌面启动。")
    app=QtWidgets.QApplication(sys.argv)
    window=Window(); window.show()
    sys.exit(app.exec())

if __name__=="__main__":
    main()
