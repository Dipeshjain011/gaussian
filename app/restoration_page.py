from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtWidgets import (QComboBox,QDoubleSpinBox,QFileDialog,QFormLayout,QGridLayout,QHBoxLayout,QLabel,QMessageBox,QProgressBar,QPushButton,QScrollArea,QVBoxLayout,QWidget)
from utils.thread_utils import TaskController
from workers.image_worker import load_image_task
from workers.restoration_worker import blur_task,noise_task,restore_task
from .widgets import Card,ImagePanel

class RestorationPage(QWidget):
    def __init__(self,state):
        super().__init__(); self.state=state; self.pending_action=""; self.pending_path=""; self.controller=TaskController(self)
        root=QVBoxLayout(self); title=QLabel("Image Restoration"); title.setObjectName("pageTitle"); root.addWidget(title)
        scroll=QScrollArea(widgetResizable=True); scroll.setFrameShape(QScrollArea.NoFrame); root.addWidget(scroll); body=QWidget(); scroll.setWidget(body); layout=QVBoxLayout(body)
        controls=Card("Input and degradation controls"); row=QHBoxLayout(); self.mode=QComboBox(); self.mode.addItems(["Controlled experiment (original image)","Real blurred image (no ground truth)"]); self.choose=QPushButton("Choose Image"); self.clear=QPushButton("Clear")
        row.addWidget(QLabel("Mode")); row.addWidget(self.mode,1); row.addWidget(self.choose); row.addWidget(self.clear); controls.layout.addLayout(row)
        form=QFormLayout(); self.kernel=QComboBox(); self.kernel.addItems(["3","5","7","9","11","15","21"]); self.kernel.setCurrentText("15")
        self.sigma=QDoubleSpinBox(); self.sigma.setRange(.1,10); self.sigma.setValue(3); self.sigma.setSingleStep(.1)
        self.noise=QDoubleSpinBox(); self.noise.setRange(0,1); self.noise.setDecimals(3); self.noise.setSingleStep(.01)
        self.threshold=QDoubleSpinBox(); self.threshold.setRange(.0001,.1); self.threshold.setDecimals(4); self.threshold.setValue(.01)
        self.wiener_k=QDoubleSpinBox(); self.wiener_k.setRange(.000001,1); self.wiener_k.setDecimals(6); self.wiener_k.setValue(.01)
        for label,widget in (("Gaussian kernel",self.kernel),("Sigma (σ)",self.sigma),("Noise level",self.noise),("Inverse H threshold",self.threshold),("Wiener K",self.wiener_k)): form.addRow(label,widget)
        controls.layout.addLayout(form); buttons=QHBoxLayout(); self.blur_btn=QPushButton("Apply Gaussian Blur"); self.noise_btn=QPushButton("Apply Noise"); self.inverse_btn=QPushButton("Restore Using Inverse Filter"); self.wiener_btn=QPushButton("Restore Using Wiener Filter"); self.action_buttons=(self.choose,self.clear,self.blur_btn,self.noise_btn,self.inverse_btn,self.wiener_btn)
        for button in self.action_buttons[2:]: buttons.addWidget(button)
        controls.layout.addLayout(buttons); status=QHBoxLayout(); self.progress=QProgressBar(); self.progress.hide(); self.cancel_btn=QPushButton("Cancel Processing"); self.cancel_btn.hide(); self.cancel_btn.clicked.connect(self.controller.cancel); status.addWidget(self.progress,1); status.addWidget(self.cancel_btn); controls.layout.addLayout(status)
        self.details=QLabel("No image selected"); self.details.setObjectName("muted"); controls.layout.addWidget(self.details); layout.addWidget(controls)
        grid=QGridLayout(); self.original_panel=ImagePanel("ORIGINAL / INPUT"); self.degraded_panel=ImagePanel("BLURRED / DEGRADED"); self.inverse_panel=ImagePanel("INVERSE FILTER RESULT"); self.wiener_panel=ImagePanel("WIENER FILTER RESULT")
        for panel,r,c in ((self.original_panel,0,0),(self.degraded_panel,0,1),(self.inverse_panel,1,0),(self.wiener_panel,1,1)): grid.addWidget(panel,r,c)
        layout.addLayout(grid); self.choose.clicked.connect(self.load_image); self.clear.clicked.connect(self.clear_all); self.mode.currentIndexChanged.connect(self.mode_changed); self.blur_btn.clicked.connect(self.apply_blur); self.noise_btn.clicked.connect(self.apply_noise); self.inverse_btn.clicked.connect(lambda:self.run_restore("inverse")); self.wiener_btn.clicked.connect(lambda:self.run_restore("wiener"))
        self.controller.progress.connect(self.on_progress); self.controller.result.connect(self.on_result); self.controller.error.connect(self.on_error); self.controller.cancelled.connect(lambda:self.state.message.emit("Processing cancelled.")); self.controller.busy_changed.connect(self.set_busy); self.state.changed.connect(self.refresh)
    def start(self,action,task): self.pending_action=action; self.controller.start(task)
    def set_busy(self,busy):
        for b in self.action_buttons:b.setEnabled(not busy)
        self.progress.setVisible(busy); self.cancel_btn.setVisible(busy)
        if not busy:self.progress.setValue(0)
    def on_progress(self,value,message):self.progress.setValue(value);self.state.message.emit(message)
    def on_error(self,message):QMessageBox.warning(self,"Unable to process image",message);self.state.message.emit("Operation failed. Please check the input and try again.")
    def load_image(self):
        path,_=QFileDialog.getOpenFileName(self,"Choose image","","Images (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)")
        if path:self.pending_path=path;self.start("load",load_image_task(path,2048))
    def apply_blur(self):
        d=self.state.data
        if d.original is None:return self.on_error("Choose an image first.")
        if not d.controlled:return self.on_error("Use Controlled Experiment mode to create Gaussian blur.")
        d.kernel_size=int(self.kernel.currentText());d.sigma=self.sigma.value();d.noise=0;self.start("blur",blur_task(d.original,d.kernel_size,d.sigma))
    def apply_noise(self):
        d=self.state.data
        if d.degraded is None:return self.on_error("Create or load a degraded image first.")
        d.noise=self.noise.value();self.start("noise",noise_task(d.degraded,d.noise))
    def run_restore(self,method):
        d=self.state.data
        if d.degraded is None:return self.on_error("Create or load a degraded image first.")
        d.kernel_size=int(self.kernel.currentText());d.sigma=self.sigma.value();p=self.threshold.value() if method=="inverse" else self.wiener_k.value();self.start(method,restore_task(method,d.degraded,d.original,d.controlled,d.kernel_size,d.sigma,p,d.otf,d.noise))
    def on_result(self,result):
        d=self.state.data;a=self.pending_action
        if a=="load":
            d.path=self.pending_path;d.original=result["image"];d.controlled=self.mode.currentIndex()==0;d.degraded=None if d.controlled else d.original.copy()
            if result["original_shape"][:2]!=d.original.shape[:2]:QMessageBox.information(self,"Large image detected",f"A {result['original_shape'][1]} × {result['original_shape'][0]} image was loaded as a {d.original.shape[1]} × {d.original.shape[0]} working copy. The source file was not modified.")
        elif a=="blur":d.degraded=result["degraded"];d.otf=result["otf"]
        elif a=="noise":d.degraded=result
        else:setattr(d,a,result["image"]);setattr(d,f"{a}_response",result["response"]);setattr(d,f"{a}_time",result["time"]);setattr(d,f"{a}_metrics",result["metrics"]);d.otf=result["otf"]
        if a in ("load","blur","noise"):d.inverse=d.wiener=None;d.inverse_metrics=d.wiener_metrics=None;d.inverse_response=d.wiener_response=None
        self.state.notify({"load":"Image loaded successfully","blur":"Gaussian blur applied","noise":"Gaussian noise applied","inverse":"Inverse filtering completed","wiener":"Wiener filtering completed"}[a])
    def mode_changed(self):
        if self.controller.busy:return
        d=self.state.data;d.controlled=self.mode.currentIndex()==0
        if d.original is not None:d.degraded=None if d.controlled else d.original.copy();d.inverse=d.wiener=None;self.state.notify("Restoration mode changed")
    def clear_all(self):
        from .state import ProjectData
        self.state.data=ProjectData();self.state.notify("Project cleared")
    def refresh(self):
        d=self.state.data;self.original_panel.set_image(d.original);self.degraded_panel.set_image(d.degraded);self.inverse_panel.set_image(d.inverse);self.wiener_panel.set_image(d.wiener)
        if d.original is None:self.details.setText("No image selected");return
        h,w=d.original.shape[:2];channels=1 if d.original.ndim==2 else d.original.shape[2];size=os.path.getsize(d.path)/1024 if d.path and os.path.exists(d.path) else 0;self.details.setText(f"{Path(d.path).name if d.path else 'Image'}  •  {w} × {h}  •  {channels} channel(s)  •  {size:.1f} KB  •  Ground truth {'available' if d.controlled else 'unavailable'}")
